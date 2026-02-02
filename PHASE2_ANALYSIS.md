# Phase 2: Medium-Impact Optimizations - Analysis

**Date:** February 3, 2026  
**Status:** In Progress

## Thread Pool Usage Analysis

### Current State

**ThreadPoolExecutor instances created per component:**

1. **BaseSubscriber** (`commlib/pubsub.py:147`)
   - Default: 4 workers per subscriber
   - Per-instance creation
   - Used for: Message callback execution

2. **BaseRPCService** (`commlib/rpc.py:73`)
   - Default: 4 workers per service
   - Per-instance creation
   - Used for: RPC request handling

3. **RPCClient** (`commlib/rpc.py:191`)
   - Configurable workers (default varies)
   - Per-instance creation
   - Used for: Async RPC calls

4. **ProxyRPCService** (`commlib/rpc.py:349`)
   - Configurable workers
   - Per-instance creation
   - Used for: Proxied RPC handling

5. **GoalHandler** (`commlib/action.py:167`)
   - Fixed: 2 workers per goal
   - Created per action goal (potentially many!)
   - Used for: Goal execution and cancellation

6. **Node** (`commlib/node.py:330`)
   - Configurable: `_workers_rpc`
   - Per-node creation
   - Used for: Node-level operations

### Problem

**Scenario:** Node with 10 subscribers + 5 RPC services + 3 actions (each with 5 concurrent goals)

Thread count:
- 10 subscribers × 4 workers = 40 threads
- 5 RPC services × 4 workers = 20 threads
- 1 node executor × workers_rpc = ~8 threads
- 3 actions × 5 goals × 2 workers = 30 threads
- **Total: ~98 threads** for a single node!

### Issues

1. **Thread Exhaustion:** System limits typically 1000-4000 threads
2. **Context Switching:** Excessive switching overhead
3. **Memory Overhead:** Each thread ~8MB stack space = 784MB just for thread stacks
4. **Startup Time:** Creating 100 thread pools is slow
5. **Resource Contention:** Threads competing for CPU

---

## Busy-Wait Polling Analysis

### Locations

1. **endpoints.py:111** - Waiting for connection
   ```python
   while not self.connected:
       time.sleep(0.001)  # 1000 wake-ups per second!
   ```

2. **endpoints.py:130** - Waiting for disconnection
   ```python
   while self.connected:
       time.sleep(0.001)  # 1000 wake-ups per second!
   ```

3. **node.py:342, 348** - Waiting for health check
   ```python
   while not self.health:
       time.sleep(0.01)  # 100 wake-ups per second
   ```

4. **kafka.py:385, 501, 572** - Kafka consumer polling
   ```python
   time.sleep(0.001)  # 1000 wake-ups per second
   ```

5. **bridges.py:151** - Bridge polling
   ```python
   time.sleep(0.001)  # 1000 wake-ups per second
   ```

### Problem

**Impact:** A single subscriber waiting for connection:
- 1000 wake-ups/second × 1ms sleep = wasted CPU cycles
- Better: Use threading.Event or asyncio for event-driven waiting

---

## Redis Connection Pool Analysis

### Current State

Each Redis transport instance creates its own connection pool:

**File:** `commlib/transports/redis.py`

Multiple instances:
- Each Subscriber creates new Redis client
- Each Publisher creates new Redis client
- No connection sharing between instances

### Problem

**Scenario:** 20 subscribers + 10 publishers using Redis

- 30 independent Redis connections
- Each with own connection pool (default 50 connections per pool)
- Potential: 30 × 50 = 1500 connections to Redis!
- Redis default max: 10,000 connections (but many fewer in practice)

### Opportunity

- Share connection pool across all Redis transports
- Reduces connection count by 10-30x
- Faster connection acquisition
- Better resource utilization

---

## Optimization Plan

### Task 1: Shared Thread Pool (High Priority)

**Goal:** Reduce from ~100 threads to ~10-20 threads per node

**Approach:**
1. Create global thread pool manager (`commlib/thread_pool.py`)
2. Singleton pattern with configurable pool sizes
3. Categories:
   - **IO Pool:** For message handling (subscribers, RPC)
   - **Compute Pool:** For heavy callbacks
   - **Action Pool:** For action goal execution
4. Backwards compatible: Optional shared pool usage

**Implementation:**
```python
# commlib/thread_pool.py
class ThreadPoolManager:
    _instance = None
    _io_pool = None
    _compute_pool = None
    _action_pool = None
    
    @classmethod
    def get_io_pool(cls, max_workers=None):
        if cls._io_pool is None:
            cls._io_pool = ThreadPoolExecutor(
                max_workers=max_workers or (os.cpu_count() * 2)
            )
        return cls._io_pool
```

**Changes Required:**
- `commlib/pubsub.py`: Use shared pool
- `commlib/rpc.py`: Use shared pool
- `commlib/action.py`: Use shared pool (or per-goal pool with limits)
- `commlib/node.py`: Use shared pool

**Testing:**
- Verify no deadlocks
- Test concurrent subscribers/services
- Benchmark throughput before/after

---

### Task 2: Event-Driven Waiting (High Priority)

**Goal:** Eliminate busy-wait polling (1000+ wake-ups/sec → 0)

**Approach:**
1. Replace `while not connected: time.sleep(0.001)` with `threading.Event`
2. Modify transports to signal events on state changes
3. Use event.wait(timeout) instead of polling

**Implementation:**
```python
# In BaseTransport
class BaseTransport:
    def __init__(self):
        self._connected_event = threading.Event()
    
    def start(self):
        # ... connection logic
        self._connected_event.set()
    
    def stop(self):
        self._connected_event.clear()

# In endpoints.py
def run(self, wait=True):
    self._transport.start()
    if wait:
        # Old: while not self.connected: time.sleep(0.001)
        # New:
        self._transport._connected_event.wait(timeout=10)
```

**Changes Required:**
- `commlib/transports/base_transport.py`: Add event attributes
- `commlib/endpoints.py`: Use events instead of polling
- `commlib/node.py`: Use events for health checks

---

### Task 3: Redis Connection Pool Sharing (Medium Priority)

**Goal:** Reduce Redis connections by 10-30x

**Approach:**
1. Create connection pool registry
2. Key by (host, port, db)
3. Share pools across instances
4. Reference counting for cleanup

**Implementation:**
```python
# commlib/transports/redis.py
_REDIS_POOLS = {}
_REDIS_POOL_LOCK = threading.Lock()

def get_or_create_redis_pool(host, port, db, **kwargs):
    key = (host, port, db)
    with _REDIS_POOL_LOCK:
        if key not in _REDIS_POOLS:
            _REDIS_POOLS[key] = redis.ConnectionPool(
                host=host, port=port, db=db, **kwargs
            )
        return _REDIS_POOLS[key]
```

**Changes Required:**
- `commlib/transports/redis.py`: Implement pool sharing
- Add tests for pool reuse
- Add cleanup on last instance release

---

## Expected Improvements

### Thread Pool Consolidation
- **Before:** 50-100 threads per node
- **After:** 10-20 threads per node
- **Benefit:** 
  - 5-10x fewer threads
  - ~400-800MB memory saved per node
  - Reduced context switching overhead
  - Faster startup time

### Event-Driven Waiting
- **Before:** 1000+ wake-ups per second per waiting operation
- **After:** 0 wake-ups (event-driven)
- **Benefit:**
  - Eliminates wasted CPU cycles
  - More responsive (immediate notification vs polling interval)
  - Lower power consumption

### Redis Pool Sharing
- **Before:** 30+ independent connections
- **After:** 3-5 shared connections
- **Benefit:**
  - 6-10x fewer connections
  - Faster connection acquisition
  - Reduced Redis server load
  - Better connection reuse

---

## Overall Phase 2 Target

**Combined improvement: 20-30% additional performance gain**

- Thread reduction: 10-15% improvement (less overhead)
- Event-driven: 5-10% improvement (less wasted CPU)
- Connection pooling: 5-10% improvement (faster I/O)

**Total cumulative (Phase 1 + 2): 35-50% improvement over baseline**

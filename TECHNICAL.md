# APIKeyWall - Technical Documentation

## Architecture Overview

APIKeyWall is a mitmproxy addon that intercepts HTTP requests, checks for configured placeholder API tokens in the Authorization header, and replaces them with real tokens when the request destination matches predefined endpoints.

## Addon Structure

### Core Components:
- `ApiKeyWall` class: Main addon class implementing mitmproxy hooks
- `load()`: Initializes addon, loads config and sets `tcp_timeout` to 7200s
- `_maybe_reload()`: Periodic hook (every ~1s) that checks for config updates
- `requestheaders()`: Processes each HTTP request to swap tokens
- `_update_allow_hosts()`: Dynamically updates `ctx.options.allow_hosts`

## Configuration Management

### File Loading Mechanism:
1. **Atomic loading**: Config file is moved to a temporary location before reading
2. **Automatic cleanup**: File is deleted after reading (security feature)
3. **Hot reload**: Checks for config changes every second via `_maybe_reload()`

### JSON Schema Validation:
```json
{
  "type": "array",
  "items": {
    "type": "object",
    "properties": {
      "tokenin": {"type": "string"},
      "tokenout": {"type": "string"},
      "endpoints": {"type": "array", "items": {"type": "string"}}
    },
    "required": ["tokenin", "tokenout", "endpoints"]
  }
}
```

## Security Features

### 1. In-Memory Storage
- Real API tokens never persist to disk after initial load
- Configuration file is immediately deleted post-read
- Tokens stored in memory within the addon instance

### 2. Host Restriction
- `allow_hosts` is dynamically set to only intercept traffic to configured endpoints

### 3. Connection Management
- TCP timeout set to 7200 seconds for stable long-running connections
- Appropriate for API workloads with extended sessions

## Hook Execution Flow

```
mitmproxy start
  ↓
addon.load()                      # Set tcp_timeout = 7200
  ├── addon._reload_if_present()  # Initial config load
  ├── addon._maybe_reload()       # Every ~1s, checks config
  ↓
mitmproxy event loop
  └── requestheaders()        # For each HTTP request
        ├── Check Authorization header
        ├── Match tokenin against RULES
        ├── Verify host in endpoints
        └── Replace tokenin with tokenout
```

## Performance Characteristics

- **Memory**: Minimal - stores only active rules and endpoint list
- **CPU**: Negligible - regex matching only on token/endpoint validation
- **Network**: Adds minimal latency (header string replacement only)

## Logging

Log messages indicate:
- Configuration reload events with rule counts
- `allow_hosts` updates with endpoint counts
- File system errors during config loading
- Token replacement actions

## Advanced Configuration

### Running as a Transparent Bridge (Advanced) ###
For the highest security, you can run APIKeyWall on a dedicated gateway machine or virtual machine configured as a transparent bridge. This isolates the proxy from your workstation. Please refer to the mitmproxy [transparent mode](https://docs.mitmproxy.org/stable/concepts/modes/#transparent-proxy) documentation if you wish to explore this setup. Also check [Linux-bridge-no-IPs-ai-generated.md](Linux-bridge-no-IPs-ai-generated.md)

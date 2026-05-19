# Project Caveats

## xwl_bi

Current known local caveat:

- `C:\Users\admin\Documents\src\xwl_bi\scripts\docker-middleware.md`
- `C:\Users\admin\Documents\src\xwl_bi\scripts\kafka-dashboard.md`

These documents describe a manually deployed middleware stack on Docker Desktop, not a fully validated `deploy/` workflow.

Important implications:

- Do not assume the `deploy/` directory is the authoritative runtime path.
- Do not prune stopped `kafka`, `kafka-ui`, or `zookeeper` containers until you review the `scripts/*.md` docs and confirm they are disposable.
- `xwl_bi` expects the dedicated Docker network `xwl_bi_net`.
- `kafka-ui` expects Kafka to expose `kafka:9093` inside the Docker network and `127.0.0.1:9092` on the host.
- `clickhouse` may already be healthy and should not be restarted unless the user asks.

Known manual restore path from `scripts/*.md`:

1. Ensure Docker network `xwl_bi_net` exists.
2. Start `zookeeper` with `confluentinc/cp-zookeeper:7.5.0`.
3. Start `kafka` with dual listeners:
   - host listener `127.0.0.1:9092`
   - container listener `kafka:9093`
4. Start `kafka-ui` on port `8080`, pointed at `kafka:9093` and `zookeeper:2181`.
5. Verify the topic from `scripts/config/config.json`, which in the current notes is `test005`.

If data appears missing after container cleanup:

- first determine whether the data lived in a named volume, bind mount, or only in the removed container writable layer
- if it lived only in the container writable layer, it is not recoverable by simply recreating the container
- before further cleanup, inspect `docker volume ls`, `docker volume inspect`, and the project's docs

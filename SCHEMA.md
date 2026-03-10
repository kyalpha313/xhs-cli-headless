# Structured Output Schema

`xiaohongshu-cli` uses a shared agent-friendly envelope for machine-readable output.

## Success

```yaml
ok: true
schema_version: "1"
data: ...
```

## Error

```yaml
ok: false
schema_version: "1"
error:
  code: api_error
  message: need login
```

## Notes

- `--yaml` and `--json` both use this envelope
- non-TTY stdout defaults to YAML
- reading and search commands return their payload under `data`
- `status` returns `data.authenticated` plus `data.user`
- `whoami` returns `data.user`

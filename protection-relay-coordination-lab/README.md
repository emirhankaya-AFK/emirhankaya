# Protection Relay Coordination Lab

A small calculation tool for checking time grading between inverse-time overcurrent relays on a radial feeder.

I built this around a common protection-study question: for a fault seen by several relays, does the downstream device clear first while the upstream device keeps a usable backup delay?

## Included calculations

- IEC standard inverse, very inverse, and extremely inverse curves
- Pickup multiple and theoretical operating time for each relay
- Pairwise grading margin from load end to source
- Clear pass/fail result against a user-defined minimum margin
- Two worked feeder cases and a JSON API for custom studies

The inverse-time equation is:

```text
t = TMS × k / ((I / Is)^α - 1)
```

`k` and `α` are selected from the chosen curve family. A relay at or below pickup is reported as non-operating instead of forcing the equation near its singularity.

## Run it

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
ruff check .
pytest -q
uvicorn api.main:app --reload
```

Open `http://127.0.0.1:8000` for the dashboard or `/docs` for the API.

## Input ordering

Relay entries must be supplied from downstream to upstream. Each relay currently carries the fault current seen at its own location, which makes CT ratios and network attenuation explicit inputs rather than hidden assumptions.

## Engineering boundary

This is a study aid, not a setting approval package. It does not model breaker clearing time, relay overtravel, CT saturation, instantaneous elements, earth-fault elements, transformer inrush, arc-flash energy, or a complete short-circuit network. Real settings require the equipment curves, protection philosophy, fault study, and review by the responsible protection engineer.

## License

MIT

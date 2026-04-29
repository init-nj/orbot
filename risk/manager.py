def position_size(capital: float, risk_pct: float,
                  entry: float, stop_loss: float) -> int:
    risk_amt      = capital * risk_pct
    risk_per_unit = abs(entry - stop_loss)
    if risk_per_unit == 0:
        return 0
    return max(1, int(risk_amt / risk_per_unit))

def compute_targets(signal: str, entry: float, orb_high: float, orb_low: float,
                    rr_ratio: float = 2.0):
    if signal == 'BUY':
        stop   = orb_low
        target = entry + rr_ratio * (entry - stop)
    else:
        stop   = orb_high
        target = entry - rr_ratio * (stop - entry)
    return stop, target
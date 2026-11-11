"""Deterministic, illustrative waste and methane calculations.

IMPORTANT: The methane proxy is NOT an IPCC inventory model or measured emissions.
"""
from dataclasses import dataclass
import hashlib
import json
import math

REQUIRED = ('period','waste_tonnes','landfill_fraction','recycling_fraction','compost_fraction')

@dataclass(frozen=True)
class Assumptions:
    methane_kg_per_landfilled_tonne: float = 25.0  # illustrative only, not an official emission factor
    methane_gwp100: float = 27.0  # illustrative configurable scenario assumption


def validate_rows(rows):
    if not rows:
        raise ValueError('At least one row is required.')
    seen = set()
    clean = []
    for index, row in enumerate(rows, 1):
        for field in REQUIRED:
            if field not in row or row[field] is None or str(row[field]).strip() == '':
                raise ValueError(f'Row {index}: missing {field}.')
        period = str(row['period']).strip()
        if period in seen:
            raise ValueError(f'Row {index}: duplicate period {period}.')
        seen.add(period)
        values = {}
        for field in REQUIRED[1:]:
            try:
                value = float(row[field])
            except (ValueError, TypeError):
                raise ValueError(f'Row {index}: {field} must be numeric.') from None
            if not math.isfinite(value):
                raise ValueError(f'Row {index}: {field} must be finite.')
            values[field] = value
        if values['waste_tonnes'] < 0:
            raise ValueError(f'Row {index}: negative waste is invalid.')
        fractions = [values[k] for k in REQUIRED[2:]]
        if any(v < 0 or v > 1 for v in fractions):
            raise ValueError(f'Row {index}: fractions must be between 0 and 1.')
        if sum(fractions) > 1 + 1e-9:
            raise ValueError(f'Row {index}: destination fractions exceed 100%.')
        clean.append({'period': period, **values})
    return clean


def calculate(rows, assumptions=Assumptions()):
    if not math.isfinite(assumptions.methane_kg_per_landfilled_tonne) or assumptions.methane_kg_per_landfilled_tonne < 0:
        raise ValueError('Illustrative methane coefficient must be finite and nonnegative.')
    if not math.isfinite(assumptions.methane_gwp100) or assumptions.methane_gwp100 < 0:
        raise ValueError('GWP assumption must be finite and nonnegative.')
    output = []
    for row in validate_rows(rows):
        waste = row['waste_tonnes']
        landfill = waste * row['landfill_fraction']
        recycled = waste * row['recycling_fraction']
        composted = waste * row['compost_fraction']
        methane_kg = landfill * assumptions.methane_kg_per_landfilled_tonne
        output.append({**row, 'landfill_tonnes': landfill, 'recycled_tonnes': recycled,
                       'composted_tonnes': composted, 'other_tonnes': max(0.0, waste-landfill-recycled-composted),
                       'illustrative_methane_kg': methane_kg,
                       'illustrative_co2e_tonnes': methane_kg * assumptions.methane_gwp100 / 1000})
    return output


def totals(rows):
    keys = ('waste_tonnes','landfill_tonnes','recycled_tonnes','composted_tonnes','other_tonnes','illustrative_methane_kg','illustrative_co2e_tonnes')
    return {key: sum(row[key] for row in rows) for key in keys}


def fingerprint(payload):
    return hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False, allow_nan=False).encode('utf-8')).hexdigest()


def anomalies(rows, threshold=0.3):
    """Flag waste-volume changes relative to previous period, not statistical outliers."""
    result=[]
    for previous, current in zip(rows, rows[1:]):
        base=previous['waste_tonnes']
        if base == 0:
            if current['waste_tonnes'] > 0:
                result.append({'period':current['period'],'change_pct':None,'reason':'Increase from zero baseline'})
        else:
            change=(current['waste_tonnes']-base)/base
            if abs(change)>threshold:
                result.append({'period':current['period'],'change_pct':round(change*100,2),'reason':'Period-to-period waste change'})
    return result


def period_context(rows):
    """Small, ordered aggregate timeline for AI interpretation; no raw uploaded rows."""
    result = []
    previous = None
    for row in rows:
        current = {'period': row['period'], 'waste_tonnes': round(row['waste_tonnes'], 4)}
        if previous is not None:
            base = previous['waste_tonnes']
            current['previous_period'] = previous['period']
            current['change_pct'] = round((row['waste_tonnes'] - base) / base * 100, 2) if base else None
            current['direction'] = ('increase' if row['waste_tonnes'] > base else
                                    'decrease' if row['waste_tonnes'] < base else 'unchanged')
        result.append(current)
        previous = row
    return result


def round_for_export(value, digits=6):
    """Clean floating-point artifacts in exports without changing calculation inputs/hash."""
    if isinstance(value, dict):
        return {k: round_for_export(v, digits) for k, v in value.items()}
    if isinstance(value, list):
        return [round_for_export(v, digits) for v in value]
    if isinstance(value, float):
        return round(value, digits)
    return value

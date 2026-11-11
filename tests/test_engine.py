import pytest
from engine import Assumptions, validate_rows, calculate, totals, anomalies, fingerprint, period_context, round_for_export

ROWS=[{'period':'2026-01','waste_tonnes':100,'landfill_fraction':0.5,'recycling_fraction':0.3,'compost_fraction':0.1},
      {'period':'2026-02','waste_tonnes':150,'landfill_fraction':0.4,'recycling_fraction':0.4,'compost_fraction':0.1}]

def test_valid_rows(): assert len(validate_rows(ROWS))==2
def test_landfill(): assert calculate(ROWS)[0]['landfill_tonnes']==50
def test_methane_proxy(): assert calculate(ROWS)[0]['illustrative_methane_kg']==1250
def test_co2e_proxy(): assert calculate(ROWS)[0]['illustrative_co2e_tonnes']==33.75
def test_totals(): assert totals(calculate(ROWS))['waste_tonnes']==250
def test_anomaly(): assert len(anomalies(calculate(ROWS),0.3))==1
def test_hash_stable(): assert fingerprint(ROWS)==fingerprint(ROWS)
def test_hash_change(): assert fingerprint(ROWS)!=fingerprint(ROWS[:1])
@pytest.mark.parametrize('change', [{'waste_tonnes':-1},{'landfill_fraction':1.1},{'recycling_fraction':0.8},{'period':''},{'waste_tonnes':float('nan')}])
def test_invalid(change):
    row={**ROWS[0],**change}
    with pytest.raises(ValueError): validate_rows([row])
def test_duplicate():
    with pytest.raises(ValueError): validate_rows([ROWS[0],ROWS[0]])
def test_invalid_assumption():
    with pytest.raises(ValueError): calculate(ROWS,Assumptions(-1,27))
def test_zero_baseline_alert():
    rows=[{**ROWS[0],'waste_tonnes':0},ROWS[1]]
    assert anomalies(calculate(rows))[0]['change_pct'] is None


def test_period_context_direction_and_months():
    context = period_context(calculate(ROWS))
    assert len(context) == 2
    assert context[1]['previous_period'] == '2026-01'
    assert context[1]['change_pct'] == 50.0
    assert context[1]['direction'] == 'increase'

def test_period_context_decrease():
    context = period_context([{'period':'2026-01','waste_tonnes':180}, {'period':'2026-02','waste_tonnes':125}])
    assert context[1]['direction'] == 'decrease'
    assert context[1]['change_pct'] == -30.56

def test_round_export_nested():
    assert round_for_export({'x':493.34000000000003,'r':[14.200000000000001]}) == {'x':493.34,'r':[14.2]}

def test_round_export_preserves_hash_and_types():
    original={'dataset_sha256':'abc123','status':'needs_evidence','id':1,'amount':0.30000000000000004}
    assert round_for_export(original)=={'dataset_sha256':'abc123','status':'needs_evidence','id':1,'amount':0.3}

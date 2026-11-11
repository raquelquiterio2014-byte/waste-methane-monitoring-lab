"""Waste & Methane Monitoring Lab V1.0 — independent educational COP31 Day 3 prototype."""
import io
import json
from pathlib import Path
import pandas as pd
import streamlit as st
from engine import Assumptions, calculate, totals, anomalies, fingerprint, period_context, round_for_export
from storage import initialize, save_review, list_reviews
from ai_gateway import interpret

st.set_page_config(page_title='Waste & Methane Monitoring Lab V1.0',page_icon='♻️',layout='wide')
st.markdown('''<style>.stApp{background:linear-gradient(120deg,#071c20,#103a37);color:#e7f9f2}
[data-testid="stMetric"]{background:#123c3c;border:1px solid #2caa8c;border-radius:12px;padding:12px}</style>''',unsafe_allow_html=True)
st.title('♻️ Waste & Methane Monitoring Lab V1.0')
st.caption('COP31 AI Solutions Lab · Day 3 · Independent educational prototype · Human oversight required')
st.warning('SYNTHETIC DEMONSTRATION. Methane and CO₂e outputs are illustrative scenario proxies, NOT measured emissions or an IPCC inventory. The coefficients below are hypothetical, not official factors.')
initialize()
source=Path(__file__).parent/'sample_data'/'synthetic_waste.csv'
with st.sidebar:
    st.header('Data & assumptions')
    uploaded=st.file_uploader('Upload a CSV (or use the bundled synthetic example)',type=['csv'])
    st.caption('CSV fields: period, waste_tonnes, landfill_fraction, recycling_fraction, compost_fraction. Fractions range from 0 to 1.')
    coefficient=st.number_input('Illustrative methane kg / landfilled tonne',min_value=0.0,max_value=1000.0,value=25.0,step=1.0)
    gwp=st.number_input('Illustrative methane GWP100',min_value=0.0,max_value=1000.0,value=27.0,step=1.0)
    threshold=st.slider('Period-to-period alert threshold',min_value=5,max_value=100,value=30,step=5)
    st.caption('These values are scenario inputs only. They are not scientifically validated emission factors.')
try:
    df=pd.read_csv(uploaded if uploaded is not None else source)
    assumptions=Assumptions(coefficient,gwp)
    records=calculate(df.to_dict('records'),assumptions)
    summary=totals(records)
    alerts=anomalies(records,threshold/100)
    dataset_hash=fingerprint({'rows':records,'assumptions':assumptions.__dict__,'threshold_pct':threshold})
except (ValueError,KeyError,TypeError,pd.errors.ParserError) as exc:
    st.error(f'Invalid dataset: {exc}')
    st.stop()

tabs=st.tabs(['Overview','Waste & Methane Indicators','Trends & Alerts','Gemini AI Interpretation','Human Review & Export'])
with tabs[0]:
    st.subheader('Waste monitoring overview')
    a,b,c,d=st.columns(4)
    a.metric('Waste (tonnes)',f"{summary['waste_tonnes']:,.1f}")
    b.metric('Landfilled (tonnes)',f"{summary['landfill_tonnes']:,.1f}")
    c.metric('Recycled (tonnes)',f"{summary['recycled_tonnes']:,.1f}")
    d.metric('Periods',len(records))
    st.dataframe(df,use_container_width=True,hide_index=True)
    st.caption('Source: uploaded user CSV' if uploaded else 'Source: bundled SYNTHETIC demonstration CSV')
with tabs[1]:
    st.subheader('Illustrative scenario indicators — NOT measured emissions')
    st.metric('Illustrative methane proxy (kg CH₄)',f"{summary['illustrative_methane_kg']:,.1f}")
    st.metric('Illustrative CO₂e proxy (tonnes)',f"{summary['illustrative_co2e_tonnes']:,.2f}")
    st.latex(r'CH_4\ (kg) = Landfilled\ waste\ (t) \times Assumed\ coefficient\ (kg/t)')
    st.latex(r'CO_{2}e\ (t) = CH_4\ (kg) \times Assumed\ GWP_{100} / 1000')
    st.info('These simplified calculations omit waste composition, degradable organic carbon, decay over time, landfill gas capture, oxidation, historical deposits and other inventory requirements.')
    st.dataframe(pd.DataFrame(records),use_container_width=True,hide_index=True)
with tabs[2]:
    st.subheader('Waste quantities and alerts')
    plot=pd.DataFrame(records).set_index('period')
    st.line_chart(plot[['waste_tonnes','landfill_tonnes','recycled_tonnes']])
    st.write(f'Alerts (absolute change > {threshold}% from the previous listed period): {len(alerts)}')
    st.dataframe(pd.DataFrame(alerts),use_container_width=True,hide_index=True) if alerts else st.success('No threshold alerts in this dataset.')
    st.caption('Rows are compared in CSV order. Sort the file chronologically before analysis.')
with tabs[3]:
    st.subheader('Gemini 2.5 Flash — optional AI-assisted interpretation')
    st.caption('Only aggregate figures, alerts, assumptions and a dataset hash are sent to Gemini. Uploaded raw rows are not sent. External API use may incur charges.')
    if st.button('Generate AI interpretation',type='primary'):
        try:
            result=interpret(summary,alerts,assumptions.__dict__,dataset_hash,period_context(records))
            st.session_state['ai_result']={'hash':dataset_hash,'interpretation':result}
            st.success('AI response received. It is NOT verified; review it below.')
        except Exception as exc:
            st.error(f'AI integration failed: {exc}')
    ai=st.session_state.get('ai_result')
    if ai and ai['hash']==dataset_hash:
        st.json(ai['interpretation'])
    elif ai:
        st.warning('Inputs changed since the last AI result. Generate a new interpretation.')
with tabs[4]:
    st.subheader('Human decision and audit trail')
    st.code(dataset_hash,language='text')
    ai=st.session_state.get('ai_result')
    current_ai=ai['interpretation'] if ai and ai['hash']==dataset_hash else None
    if current_ai is None:
        st.info('No current AI interpretation. You can still review the deterministic scenario indicators.')
    decision=st.selectbox('Reviewer decision',['needs_evidence','approved','rejected'])
    note=st.text_area('Required reviewer note',placeholder='Explain what was checked and what remains unverified.')
    if st.button('Save human review'):
        try:
            save_review(dataset_hash,decision,note,round_for_export({'totals':summary,'alerts':alerts,'assumptions':assumptions.__dict__,'ai_interpretation':current_ai,'data_origin':'uploaded' if uploaded else 'synthetic'}))
            st.success('Review saved to local SQLite database.')
        except ValueError as exc:
            st.error(str(exc))
    history=list_reviews()
    st.dataframe(pd.DataFrame([{k:v for k,v in r.items() if k!='analysis_json'} for r in history]),use_container_width=True,hide_index=True)
    st.download_button('Export calculated indicators (CSV)',pd.DataFrame(round_for_export(records)).to_csv(index=False).encode(),'waste_indicators.csv','text/csv')
    st.download_button('Export current scenario (JSON)',json.dumps(round_for_export({'origin':'uploaded' if uploaded else 'synthetic','dataset_sha256':dataset_hash,'assumptions':assumptions.__dict__,'totals':summary,'alerts':alerts,'records':records}),indent=2,allow_nan=False),'waste_scenario.json','application/json')
    st.download_button('Export human audit records (JSON)',json.dumps(round_for_export(history),indent=2,ensure_ascii=False),'human_audit.json','application/json')
    st.caption('Human approval confirms a reviewer decision only; it does not certify environmental accuracy.')
st.divider()
st.caption('Evidence first. Engineering second. Measurable impact as the goal.')

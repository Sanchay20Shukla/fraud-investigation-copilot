import json
import os
import httpx
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title='Casefile | Fraud Investigation Copilot', page_icon='◈', layout='wide')
st.markdown('''<style>
.stApp {background: #0b111b; color: #e8edf5;}
[data-testid="stSidebar"] {background: #101a28; border-right: 1px solid #253145;}
h1 {letter-spacing: -1.4px; font-weight: 650 !important;}
[data-testid="stMetric"] {background: #121d2d; padding: 20px; border: 1px solid #253145; border-radius: 12px;}
.eyebrow {color: #6ed7bd; letter-spacing: 3px; font-size: 11px; font-weight: 700; margin-bottom: 8px;}
.lede {color: #92a4bb; font-size: 16px; margin-bottom: 28px;}
</style>''', unsafe_allow_html=True)

BASE = os.getenv('API_BASE_URL', 'http://127.0.0.1:8010').rstrip('/')


def request(method, path, body=None):
    try:
        response = httpx.request(method, BASE + path, json=body, timeout=60)
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as exc:
        try:
            detail = exc.response.json().get('detail', 'Request failed')
        except ValueError:
            detail = 'The API returned an unexpected error'
        st.error(str(detail))
    except httpx.RequestError:
        st.error('Cannot reach the API. Start the backend on port 8010 and retry.')
    return None


def show_report(report):
    risk, tx = report['risk'], report['transaction']
    st.markdown(f"### {report['transaction_id']} · Investigation")
    cols = st.columns(4)
    cols[0].metric('RISK SCORE · ' + risk['risk_level'], f"{risk['risk_score']} / 100")
    cols[1].metric('AMOUNT', f"{tx['amount']:,.2f}")
    cols[2].metric('TRANSACTION TYPE', tx['transaction_type'])
    estimate = '≥99.9%' if risk['fraud_probability'] >= .999 else f"{risk['fraud_probability']:.1%}"
    cols[3].metric('MODEL ESTIMATE', estimate)
    st.caption('Amounts in simulation units · Uncalibrated model estimate · A high score does not confirm fraud')
    st.info(report['recommendation'].replace('_', ' '))
    tabs = st.tabs(['Investigation brief', 'Model explanation', 'Account history', 'Policy evidence'])
    with tabs[0]:
        st.write(report['summary'])
        for fact in report['indicators']:
            st.markdown(f"- {fact['text']}")
            st.caption('Evidence: ' + ', '.join(fact['sources']))
        st.caption(' → '.join(report['workflow']))
        if report.get('generation_warning'):
            st.warning(report['generation_warning'])
        st.caption('Generation: ' + report['generation_mode'])
        with st.expander('Scope and limitations'):
            for line in report['limitations']:
                st.write('• ' + line)
    with tabs[1]:
        drivers = pd.DataFrame(risk['drivers'][:10]).sort_values('shap_value')
        fig = px.bar(drivers, x='shap_value', y='feature', orientation='h', color='direction',
                     color_discrete_map={'increases risk': '#f28f87', 'decreases risk': '#6ed7bd'},
                     labels={'shap_value': 'Contribution to model log-odds', 'feature': ''})
        fig.update_layout(template='plotly_dark', paper_bgcolor='#0b111b', plot_bgcolor='#0b111b', height=440,
                          legend=dict(orientation='h', y=1.12), margin=dict(l=0, r=10, t=30, b=0))
        st.plotly_chart(fig, use_container_width=True)
        st.caption(risk['shap_units'])
        st.caption('Model version: ' + risk['model_version'])
    with tabs[2]:
        st.write(f"Origin: {tx['origin_account']} → Destination: {tx['destination_account']}")
        st.json(report['velocity'], expanded=True)
        if report['history']:
            st.dataframe(report['history'], use_container_width=True, hide_index=True)
        else:
            st.info('No earlier origin-account transactions in the loaded data. Account age cannot be inferred.')
    with tabs[3]:
        for source in report['sources']:
            if source['kind'] == 'policy':
                with st.expander(f"{source['source']} · {source['section']}"):
                    st.write(source['content'])
                    st.caption(f"Chunk {source['id']} · SHA-256 {source['digest']}")
    st.download_button('Download investigation JSON', json.dumps(report, indent=2),
                       file_name=report['transaction_id'] + '-investigation.json', mime='application/json')


with st.sidebar:
    st.markdown('## ◈ Casefile')
    st.caption('FRAUD INVESTIGATION COPILOT')
    st.divider()
    with st.form('investigate'):
        transaction_id = st.text_input('Transaction ID', value='TXN_0000002', max_chars=11)
        submitted = st.form_submit_button('Investigate transaction', use_container_width=True, type='primary')
    if st.button('Start a new conversation', use_container_width=True):
        for key in ['session_id', 'messages', 'report']:
            st.session_state.pop(key, None)
        st.rerun()
    st.divider()
    st.caption('TRY A FOLLOW-UP')
    st.write('Show previous transactions for this account')
    st.write('Which accounts sent to this destination?')
    st.write('What is the high-risk escalation policy?')
    st.divider()
    st.caption('Synthetic policies · PaySim data\n\nAnalyst decision support only')

st.markdown('<div class="eyebrow">EVIDENCE BEFORE CONCLUSIONS</div>', unsafe_allow_html=True)
st.title('Every alert deserves a clear explanation.')
st.markdown('<div class="lede">Transaction evidence, model drivers and policy context — in one investigation.</div>', unsafe_allow_html=True)

if submitted:
    with st.spinner('Collecting transaction, model and policy evidence…'):
        result = request('POST', '/chat', {'question': 'Investigate ' + transaction_id,
                                         'session_id': st.session_state.get('session_id')})
    if result and result.get('report'):
        st.session_state.update(report=result['report'], session_id=result['session_id'])

if 'report' in st.session_state:
    show_report(st.session_state.report)
else:
    a, b, c = st.columns(3)
    a.info('01 · Find a transaction\n\nEnter its ID to open a case.')
    b.info('02 · Follow the evidence\n\nInspect model drivers and cited policies.')
    c.info('03 · Make the judgment\n\nExport the report for analyst review.')

st.divider()
st.subheader('Ask the copilot')
for message in st.session_state.get('messages', []):
    with st.chat_message(message['role']):
        st.write(message['content'])
        if message.get('data'):
            st.json(message['data'], expanded=False)
if question := st.chat_input('Ask about this case or an investigation policy'):
    messages = st.session_state.setdefault('messages', [])
    messages.append({'role': 'user', 'content': question})
    with st.spinner('Checking the evidence…'):
        result = request('POST', '/chat', {'question': question, 'session_id': st.session_state.get('session_id')})
    if result:
        st.session_state.session_id = result['session_id']
        if result.get('report'):
            st.session_state.report = result['report']
        messages.append({'role': 'assistant', 'content': result['answer'],
                         'data': {k: v for k, v in result.items() if k not in ['answer', 'session_id', 'report']}})
    st.rerun()

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from fpdf import FPDF
from io import BytesIO
import tempfile

# --------------------- Load dari Excel ---------------------
@st.cache_data
def load_questions_from_excel(file_path):
    q_df = pd.read_excel(file_path, sheet_name='Questions')
    a_df = pd.read_excel(file_path, sheet_name='Answers')
    
    merged = q_df.merge(a_df, left_on='id', right_on='question_id')
    questions = {}
    for _, row in merged.iterrows():
        qid = row['id']
        if qid not in questions:
            questions[qid] = {
                'text': row['question_text'],
                'options': {}
            }
        questions[qid]['options'][row['vark_type']] = row['answer_text']
    return questions

# --------------------- Fungsi PDF ---------------------
def generate_pdf(name, counts, chart_buf):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    pdf.cell(200, 10, txt=f"Hasil Kuisioner VARK - {name}", ln=True, align='C')
    pdf.ln(10)

    for tipe, skor in counts.items():
        pdf.cell(200, 10, txt=f"{tipe}: {skor}", ln=True)

    # Simpan gambar chart ke file sementara sebelum ditambahkan ke PDF
    if chart_buf is not None:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmpfile:
            tmpfile.write(chart_buf.getbuffer())
            tmpfile_path = tmpfile.name
        pdf.image(tmpfile_path, x=30, w=150)

    output = BytesIO()
    pdf.output(output)
    output.seek(0)
    return output

# --------------------- Streamlit App ---------------------
st.title("Kuesioner Gaya Belajar VARK")
name = st.text_input("Masukkan Nama Anda:")

questions = load_questions_from_excel("vark_questions.xlsx")

responses = {}
with st.form("quiz_form"):
    for qid in sorted(questions):
        q = questions[qid]
        st.write(f"**{qid}. {q['text']}**")
        responses[qid] = st.radio(
            "", 
            options=list(q['options'].keys()), 
            format_func=lambda x: q['options'][x], 
            key=f"q{qid}"
        )
    submitted = st.form_submit_button("Kirim")

if submitted and name:
    counts = {'V': 0, 'A': 0, 'R': 0, 'K': 0}
    for ans in responses.values():
        counts[ans] += 1

    st.subheader("Hasil Anda")
    for k, label in zip(['V','A','R','K'], ['Visual', 'Auditory', 'Reading/Writing', 'Kinesthetic']):
        st.write(f"**{label}**: {counts[k]}")

    fig, ax = plt.subplots()
    labels = ['Visual', 'Auditory', 'Reading/Writing', 'Kinesthetic']
    values = [counts['V'], counts['A'], counts['R'], counts['K']]
    colors = ['#76c7c0', '#ffa07a', '#d8bfd8', '#fdd835']
    ax.pie(values, labels=labels, colors=colors, autopct='%1.1f%%',
           startangle=90, wedgeprops=dict(width=0.4))
    ax.axis('equal')
    st.pyplot(fig)

    chart_buf = BytesIO()
    fig.savefig(chart_buf, format='png')
    chart_buf.seek(0)

    pdf_data = generate_pdf(name, counts, chart_buf)
    st.download_button("📄 Unduh PDF", data=pdf_data, file_name="hasil_vark.pdf", mime="application/pdf")

elif submitted:
    st.warning("Silakan isi nama terlebih dahulu.")


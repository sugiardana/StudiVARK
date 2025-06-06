import streamlit as st
import pandas as pd
import random
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
                'options': []
            }
        questions[qid]['options'].append({
            'vark_type': row['vark_type'],
            'answer_text': row['answer_text']
        })
    
    # Ubah dict ke list
    questions_list = list(questions.values())
    
    # Acak pilihan jawaban setiap pertanyaan
    for q in questions_list:
        random.shuffle(q['options'])
    
    # Acak urutan pertanyaan
    random.shuffle(questions_list)
    
    return questions_list

# --------------------- Fungsi PDF ---------------------
def generate_pdf(name, counts, chart_buf):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=14)
    pdf.cell(200, 10, txt="Hasil Kuesioner VARK", ln=1, align="C")
    pdf.ln(5)
    pdf.cell(200, 10, txt=f"Nama: {name}", ln=1)
    pdf.ln(5)
    for k, label in zip(['V','A','R','K'], ['Visual', 'Auditory', 'Reading/Writing', 'Kinesthetic']):
        pdf.cell(200, 10, txt=f"{label}: {counts[k]}", ln=1)
    pdf.cell(200, 10, txt="DEBUG: Loop dengan label dipakai", ln=1)


    # Simpan chart ke file sementara
    if chart_buf is not None:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmpfile:
            tmpfile.write(chart_buf.getbuffer())
            tmpfile_path = tmpfile.name
        pdf.image(tmpfile_path, x=30, w=150)

    # ✅ Simpan hasil PDF ke BytesIO
    pdf_bytes = pdf.output(dest='S').encode('latin-1')
    output = BytesIO(pdf_bytes)
    return output

# --------------------- Streamlit App ---------------------
st.title("Kuesioner Gaya Belajar VARK")
name = st.text_input("Masukkan Nama Anda:")

questions = load_questions_from_excel("vark_questions.xlsx")

responses = {}
with st.form("quiz_form"):
    for idx, q in enumerate(questions, 1):
        st.write(f"**{idx}. {q['text']}**")
        labels = [opt['answer_text'] for opt in q['options']]
        values = [opt['vark_type'] for opt in q['options']]
        selected = st.radio(
            "", 
            options=labels,
            key=f"q{idx}"
        )
        responses[idx] = values[labels.index(selected)]

    submitted = st.form_submit_button("Kirim")

if submitted and name:
    counts = {'V': 0, 'A': 0, 'R': 0, 'K': 0}
    for ans in responses.values():
        counts[ans] += 1

    st.subheader("Hasil Anda")
    for k, label in zip(['V','A','R','K'], ['Visual', 'Auditory', 'Reading/Writing', 'Kinesthetic']):
        st.write(f"**{label}**: {counts[k]}")

    # Grafik donut
    fig, ax = plt.subplots()
    labels = ['Visual', 'Auditory', 'Reading/Writing', 'Kinesthetic']
    values = [counts['V'], counts['A'], counts['R'], counts['K']]
    colors = ['#76c7c0', '#ffa07a', '#d8bfd8', '#fdd835']
    ax.pie(values, labels=labels, colors=colors, autopct='%1.1f%%',
           startangle=90, wedgeprops=dict(width=0.4))
    ax.axis('equal')
    st.pyplot(fig)

    # Simpan grafik sebagai PNG
    chart_buf = BytesIO()
    fig.savefig(chart_buf, format='png')
    chart_buf.seek(0)

    # PDF download
    pdf_data = generate_pdf(name, counts, chart_buf)
    st.download_button("📄 Unduh PDF", data=pdf_data, file_name="hasil_vark.pdf", mime="application/pdf")

elif submitted:
    st.warning("Silakan isi nama terlebih dahulu.")


import os
#import magic
import urllib.request
from app import app
from flask import Flask, flash, request, redirect, url_for,render_template
from werkzeug.utils import secure_filename

ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])

def allowed_file(filename):
	return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
	
@app.route('/')
def upload_form():
	return render_template('disp1.html')

@app.route('/', methods=['POST'])
def upload_file():
	global fname
	fname=''
	if request.method == 'POST':
        # check if the post request has the file part
		if 'file' not in request.files:
			flash('No file part')
			return redirect(request.url)
		file = request.files['file']
		if file.filename == '':
			flash('No file selected for uploading')
			return redirect(request.url)
		if file and allowed_file(file.filename):
			filename = secure_filename(file.filename)
			file.save("D:/resume_analysis/static/resumes/"+filename)
			fname=filename
			flash('File successfully uploaded')
			
			return redirect('/disp1')
		else:
			flash('Allowed file types are txt, pdf, png, jpg, jpeg, gif')
			return redirect(request.url)
@app.route('/disp1')
def disp1():
        import io
        from pdfminer.converter import TextConverter
        from pdfminer.pdfinterp import PDFPageInterpreter
        from pdfminer.pdfinterp import PDFResourceManager
        from pdfminer.layout import LAParams
        from pdfminer.pdfpage import PDFPage
        text=''
        def extract_text_from_pdf(pdf_path):
            with open(pdf_path, 'rb') as fh:
                # iterate over all pages of PDF document
                for page in PDFPage.get_pages(fh, caching=True, check_extractable=True):
                    # creating a resoure manager
                    resource_manager = PDFResourceManager()
                    
                    # create a file handle
                    fake_file_handle = io.StringIO()
                    
                    # creating a text converter object
                    converter = TextConverter(
                                        resource_manager, 
                                        fake_file_handle, 
                                        codec='utf-8', 
                                        laparams=LAParams()
                                )

                    # creating a page interpreter
                    page_interpreter = PDFPageInterpreter(
                                        resource_manager, 
                                        converter
                                    )

                    # process current page
                    page_interpreter.process_page(page)
                    
                    # extract text
                    text = fake_file_handle.getvalue()
                    yield text

                    # close open handles
                    converter.close()
                    fake_file_handle.close()

        # calling above function and extracting text
        #print(fname)
        file_path="D:/resume_analysis/static/resumes/"+fname
        fp=file_path.split('/')
        f=fp[len(fp)-1]
        for page in extract_text_from_pdf(file_path):
            text += ' ' + page
        #print(text)
        import spacy
        from spacy.matcher import Matcher

        # load pre-trained model
        nlp = spacy.load('en_core_web_sm')

        # initialize matcher with a vocab
        matcher = Matcher(nlp.vocab)

        def extract_name(resume_text):
            nlp_text = nlp(resume_text)
            
            # First name and Last name are always Proper Nouns
            pattern = [ {'POS': 'PROPN'}, {'POS': 'PROPN'}]
            
            matcher.add('NAME', None, pattern)
            
            matches = matcher(nlp_text)
            
            for match_id, start, end in matches:
                span = nlp_text[start:end]
                return span.text
        name=extract_name(text)
        #print(name)
        import re

        def extract_mobile_number(text):
            phone = re.findall(re.compile(r'(?:(?:\+?([1-9]|[0-9][0-9]|[0-9][0-9][0-9])\s*(?:[.-]\s*)?)?(?:\(\s*([2-9]1[02-9]|[2-9][02-8]1|[2-9][02-8][02-9])\s*\)|([0-9][1-9]|[0-9]1[02-9]|[2-9][02-8]1|[2-9][02-8][02-9]))\s*(?:[.-]\s*)?)?([2-9]1[02-9]|[2-9][02-9]1|[2-9][02-9]{2})\s*(?:[.-]\s*)?([0-9]{4})(?:\s*(?:#|x\.?|ext\.?|extension)\s*(\d+))?'), text)
            
            if phone:
                number = ''.join(phone[0])
                if len(number) > 10:
                    return '+' + number
                else:
                    return number
        num=extract_mobile_number(text)
        #print(num)
        import re

        def extract_email(email):
            email = re.findall("([^@|\s]+@[^@]+\.[^@|\s]+)", email)
            if email:
                try:
                    return email[0].split()[0].strip(';')
                except IndexError:
                    return None
        email=extract_email(text)
        #print(email)
        import pandas as pd
        import spacy
        #from spacy.en import English
        # load pre-trained model
        nlp = spacy.load('en_core_web_sm')
        #noun_chunk = nlp.noun_chunks
        #nlp=English()
        doc=nlp(text)
        def extract_skills(resume_text):
            nlp_text = nlp(resume_text)

            # removing stop words and implementing word tokenization
            tokens = [token.text for token in nlp_text if not token.is_stop]
            #print(tokens)
            # reading the csv file
            data = pd.read_csv("D:/resume_analysis/techskill.csv") 
            
            # extract values
            skills = list(data.columns.values)
            
            skillset = []
            
            # check for one-grams (example: python)
            for token in tokens:
                if token.lower() in skills:
                    skillset.append(token)
            
            # check for bi-grams and tri-grams (example: machine learning)
            for token in doc.noun_chunks:
                token = token.text.lower().strip()
                if token in skills:
                    skillset.append(token)
            
            return [i.capitalize() for i in set([i.lower() for i in skillset])]
        text=text.lower()
        skill=extract_skills(text)
        print(skill)
        
        skill_len=len(skill)
        excel_file = 'D:/resume_analysis/jd.xls'
        jd = pd.read_excel(excel_file)
        skill1=jd['Skills']
        row=jd.shape[0]
        res=[]
        
        for i in range(row):
                count=0
                sk=skill1[i].split(',')
                for j in skill:
                        if(skill1[i].find(j)!=-1):
                                count=count+1
                                
                res.append(100*count/len(skill))
        ind=res.index(max(res))
        print(jd['JobTitle'][ind])
        res1=[]
        for i in res:
                res1.append(i)
        res1=sorted(res1)
        p1=max(res)
        print(res1)
        second=res1[len(res1)-1]
        third=res1[len(res1)-2]
        print(max(res),second,third)
        res[ind]=-res[ind]
        ind1=res.index(second)
        res[ind1]=-res[ind1]
        ind2=res.index(third)
        print(ind1)
        s1=jd['Skills'][ind]
        s2=jd['Skills'][ind1]
        s3=jd['Skills'][ind2]
        rs1,rs2,rs3=[],[],[]
        
        for j in skill:
                if(j in s1):
                        rs1.append(j)
        for j in skill:
                if(j in s2):
                        rs2.append(j)
        for j in skill:
                if(j in s3):
                        rs3.append(j)                
        return render_template('car.html' ,job1=jd['JobTitle'][ind],skills1=rs1,job2=jd['JobTitle'][ind1],skills2=rs2,job3=jd['JobTitle'][ind2],skills3=rs3,p1=round(p1,3),fnam=f,p2=round(second,3),p3=round(third,3))			
"""@app.route('/show/<filename>')
def uploaded_file(filename):
    filename = 'http://127.0.0.1:5000/uploads/' + filename
    return render_template('frontendproject.html', filename=filename)

@app.route('/uploads/<filename>')
def send_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)	
@app.route('/cool_form', methods=['GET', 'POST'])
def load():
    if request.method == 'POST':
        # do stuff when the form is submitted

        # redirect to end the POST handling
        # the redirect can be to the same route or somewhere else
        return redirect(url_for('index'))

    # show the form, it wasn't submitted
    return render_template('load.html')
"""
if __name__ == "__main__":
    app.run(debug=True)

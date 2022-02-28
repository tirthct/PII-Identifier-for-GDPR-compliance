from nltk.tag import StanfordNERTagger
from nltk.tokenize import word_tokenize
import glob
import os
java_path = r"C:\Program Files\Java\jdk1.8.0_161\bin\java.exe"
os.environ['JAVAHOME'] = java_path
def extract_names_from_text():


    stanford_classifier = r'C:\Program Files (x86)\stanford-ner-2018-02-27\stanford-ner-2018-02-27\classifiers\english.all.3class.distsim.crf.ser.gz'
    stanford_ner_path = r'C:\Program Files (x86)\stanford-ner-2018-02-27\stanford-ner-2018-02-27\stanford-ner.jar'
    #print("Inside def")
# Creating Tagger Object
    st = StanfordNERTagger(stanford_classifier, stanford_ner_path, encoding='utf-8')
    text_file_path = r"C:\Users\tirtht\PycharmProjects\DeepDream\ocr.txt"
    text1 = open(text_file_path, "r",encoding="utf8")
    #print(text1.read(10))
    filename = text_file_path.split("\\")[-1]

    for lines in text1:
        # print(lines)
        tokenized_text = word_tokenize(lines)
        classified_text = st.tag(tokenized_text)
        for text in classified_text:
            #print(text)
            if (text[1] == "PERSON"):
                file = open(r"C:\Users\tirtht\PycharmProjects\DeepDream\nlp_names\\"+filename, "a+")
                file.write(text[0]+"\n")

#extract_names_from_text()


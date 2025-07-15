# DS1 You must choose the correct dataset corresponding to your student number + 2 modulo 4
# input your student number and + number, WAKY will generate he number of dataset you should use
# DS2 When generating a random number you must set the seed using your student number.
# check if there is set.seed(ysn) in R script.
# DS3 Your R script must run on our machine without any errors. It must not contain any text or tex commands. It must not have any untypable characters. (You need to type everything using standard keyboard keys.)
# check if there is any '#' or any untypable characters in R script.
# DS4 Then transfer your R code to R Markdown, which must knit a PDF and not show any warnings or messages on our machine. Your R Markdown must not contain any untypable characters. Submit EXACTLY these three files (eg. no zip files) and the filenames must be of the form (remember that ysn is YOUR student number without the letter):
# check if there is any untypable characters in R markdown.
# check the name of the file, is it legal?
# it should be a1_ysn_1.R, a1_ysn_2.Rmd
# DS5 Your R script must be the same code as in the code chunks in your R Markdown file, AND your R Markdown file must knit on our machine and produce the same PDF.
# compare the code part in R markdown and R script, try to check if they are exactly the same.
# Your R Markdown cannot use any R packages from outside the course, nor should it try to install any packages. You also cannot use tex packages from outside the course --- just use the provided R Markdown template as it is.
# check the 'library' command, make sure there is no 'install' command, and compare them to the library in the course.

class WAKYError(Exception):
    pass

def DS1_checker_dataset(ysn, addnum):
    return (ysn + addnum)%4

def DS2_checker(text, ysn):
    if f'set.seed({ysn})' not in text:
        raise WAKYError

def DS3_checker_comments(text):
    if '#' in text:
        raise WAKYError

# def DS3_checker_untypable(text:str):
#     first_stage = [c for c in text if not c.isalnum()]
#     available = ['~','"',"'","|","{","}","(",")","-","+","!","@","$","%","^","&","*","=","/",":",";",",","<",">",'.','`',"#",' ','\n','_','[',']','\\','?']
#     second_stage = [c for c in first_stage if c not in available]
#     if len(second_stage) == 0:
#         return None
#     if len(second_stage)

def DS4_checker_same(r, rmd):
    
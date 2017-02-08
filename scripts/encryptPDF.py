try:
    from pyPdf import PdfFileReader, PdfFileWriter
except ImportError as e:
    print "Module: " + __name__ + "\nError: " + str(e)
    quit()

PASSWORD = "CHANGE ME"


def encrypt(path, pdf):  # change to encrypt(path, pdf):
    if PASSWORD == "CHANGE ME":
        exit(__name__+": Please set a valid password before using this module!")
    else:
        input_ = PdfFileReader(file(path+pdf, "rb"))
        output_ = PdfFileWriter()

        numPages = input_.getNumPages()

        for i in xrange(numPages):
            output_.addPage(input_.getPage(i))

        output_.encrypt(PASSWORD)
        output_.write(file(path+"enc-"+pdf, "wb"))
        file(path+"enc-"+pdf).close()   # change to path

if __name__ == '__main__':
    encrypt()
from spire.doc import *
from spire.doc.common import *

# Create a Document object
document = Document()

# Load a Doc or Docx file
document.LoadFromFile("C:\\Users\\sasha\\PycharmProjects\\amoCRM_docs\\templ_f.docx")

# Create a ToPdfParameterList object
parameter = ToPdfParameterList()

# Disable hyperlinks in generated document
parameter.DisableLink = True

# Embed fonts in generated document
parameter.IsEmbeddedAllFonts = True

# Save the Word document to PDF
document.SaveToFile("output/ToPDF.pdf", parameter)
document.Close()
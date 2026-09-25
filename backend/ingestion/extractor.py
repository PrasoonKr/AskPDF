import fitz

from backend.models.page import Page


def extract_text(pdf_path: str) -> list[Page]:
    """
    Extract text from each page of the PDF.
    """

    pdf = fitz.open(pdf_path)

    pages = []

    for page_number, page in enumerate(pdf, start=1):

        text = page.get_text().strip()

        if not text:
            continue

        pages.append(
            Page(
                number=page_number,
                text=text
            )
        )

    pdf.close()

    return pages
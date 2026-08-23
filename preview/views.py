from django.shortcuts import render

from .services.import_service import process_import


def upload_preview(request):
    """
    Display the upload form and process an uploaded HRIS CSV.
    """

    context = {}

    if request.method == "POST":

        uploaded_file = request.FILES.get("file")

        if not uploaded_file:
            context["error"] = "Please select a CSV file."

            return render(
                request,
                "preview/upload.html",
                context,
            )

        # Check file extension.
        if not uploaded_file.name.lower().endswith(".csv"):
            context["error"] = "Please upload a CSV file."

            return render(
                request,
                "preview/upload.html",
                context,
            )

        try:
            file_content = uploaded_file.read()

            result = process_import(file_content)

            context["result"] = result
            context["filename"] = uploaded_file.name

        except ValueError as exc:
            context["error"] = str(exc)

        except Exception:
            context["error"] = (
                "The uploaded file could not be processed. "
                "Please check that it is a valid HRIS CSV."
            )

    return render(
        request,
        "preview/upload.html",
        context,
    )
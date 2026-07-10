## Tax Form Preparation

Fill the official blank PDF tax forms in `forms/`. Do NOT create summary documents, Word files, or custom PDFs. The deliverable must be the actual filled-in official form(s).

**Round all dollar amounts to the nearest whole dollar.** Do not enter cents on any line.

Steps:
1. Read FORMS.md for the fillable-fields workflow.
2. Use the helper scripts in `scripts/`:
   - check_fillable_fields.py <form.pdf> — verify the form is fillable
   - extract_form_field_info.py <form.pdf> <output.json> — get field names
   - fill_pdf_fields.py — fill fields programmatically (see forms.md)
   - convert_pdf_to_images.py <form.pdf> <outdir> — render for verification
3. Find the correct blank form(s) in `forms/`.
4. Fill each form using the extracted field names and the values you compute.
5. Visually verify your filled forms by rendering them to images.
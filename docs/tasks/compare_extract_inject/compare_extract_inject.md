I need new endpoint where I can input file source, file to inject

the process should first extract from the both file

inject to the 2nd, after the inject, extract again from the new path (if changed) to compare the diff in extract results.

is that clear?

I already have extract routes thats show extracts data

```
src/templates/extract/form.html
src/templates/extract/result.html
src/main_app/public/main_routes/extract_routes.py
```

so we need simmilar files for the new endpoint.

and for inject process use inject_step_one_file.py

is this clear?

write plan for it and save it into docs folder.

example:

```
file source to extract from: File:parkinsons-disease-prevalence-ihme,World,1990.svg

file to inject: File:Parkinsons-disease-prevalence-ihme, 1990 to 2021, BMU.svg
```

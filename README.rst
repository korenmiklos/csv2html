csv2html
========
This tool converts CSV files to static webpages using Jinja templates given in a simple YAML setting file. Suppose you have a CSV file in ``books.csv`` containing::

	Author,Title,Public
	Heinrich Böll,Billiard um Halbzehn,TRUE
	Heinrich Böll,Ansichten eines Clowns,TRUE
	Bohumil Hrabal,I served the king of England,FALSE

and a YAML file in ``books.yaml`` with::

	source: books.csv
	output: books.html
	entry: |
		{{Author}} wrote "{{Title}}".
	document: |
		{% for entry in entries %}
		{% if entry.Public=="TRUE" %}{{entry}}{% endif %}
		{% endfor %}

Then saying ``python csv2html.py < books.yaml`` creates ``books.html`` with::

		Heinrich Böll wrote "Billiard um Halbzehn".
		Heinrich Böll wrote "Ansichten eines Clowns".

You get the idea. Additional features include filters applied on each field and processing multiple documents in a single YAML setting file.

Requires Jinja2_ and PyYAML_.

_Jinja2: http://jinja.pocoo.org/
_PyYAML: http://pyyaml.org/
# Bad document (deliberately broken — to see what check_md.py catches)

#### Heading level jumped (H1 straight to H4)

| Column A | Column B | Column C |
|---|---|---|
| 1 | 2 |
| 1 | 2 | 3 | 4 |

This body contains <script>alert(1)</script> and onclick="x()", both of which get sanitised away.

The formula uses x² and √2 instead of LaTeX.

\usepackage{amsmath}

A chemical formula missing a closing brace: $\ce{H2SO4$

This layout directive is invalid (only `mm`, or no unit for lines, is accepted):

[[gap:3px]]

An unclosed display formula:

$$ \int_0^1 x^2\,dx

```js
// this fence is never closed — it runs to the end of the file

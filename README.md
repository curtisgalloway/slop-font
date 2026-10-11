<h1>
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="header-dark.svg">
    <img src="header-light.svg" alt="Slop Sans" height="96">
  </picture>
</h1>

A humanist sans serif font, as drawn by an AI model that almost learned the alphabet.

## Files
- `SlopSans-Mild.ttf`, `SlopSans-Regular.ttf`, `SlopSans-Extra.ttf` — three intensities of slop (0.5 / 1.0 / 1.8).
- `SlopSans-specimen.html` — self-contained specimen with live text box and feature toggles. Open in any browser.
- `specimen-*.png` — rendered specimens.
- `slopsans.py` — the generator. `python3 slopsans.py <intensity> <StyleName> <out.ttf>` (needs fontTools, shapely).

## OpenType features
| feature | what |
|---|---|
| `calt` (on by default) | pseudo-random cycle through the 6 alternates; H M N h m n drop their right stem into a following left-stem letter |
| `ss01`–`ss06` | pin one alternate: wobble, drop+extra, melt, duplicate, gaps/overshoot, hybrid |
| `ss07` | "sober" — the unmutated humanist skeleton |
| `kern` | over-kerning fusions: stem+stem (`il ll ab`), bowl+bowl (`oo bo OO`), bar+bar (`TT ft tt`), parallel diagonals (`AV WA vv`), misreads `rn`→m, `cl`→d |

CSS: `font-feature-settings: "calt" 0, "ss03" 1;` pins the melt alternate. Set `"kern" 0` to turn fusions off.

Coverage: A–Z a–z 0–9 `. , : ; ! ? - ' " ( ) / &` and space.

## License
- Fonts (`*.ttf`, and the fonts embedded in the specimen): [SIL Open Font License 1.1](OFL.txt).
- Generator (`slopsans.py`) and everything else: [Apache License 2.0](LICENSE).

# Dataset card

## Summary

The TalTech Fish vs Drifting Debris Hackathon Dataset is a curated subset of
human-reviewed underwater monitoring frames from Fishbox annotation projects.
It targets binary screening and fish detection under real river conditions.

## Composition

Exact composition is generated in `metadata/build_report.json`. The release
contains positive frames with fish bounding boxes and reviewed no-fish hard
negatives. Negative frames are deliberately included in every split.

## Collection and annotation

Underwater cameras recorded river and fish-passage scenes. Jeffrey A. Tuhtan
created or reviewed the annotations using the Fishbox workflow. Annotation
provenance fields are retained where available. Media copyright belongs to
Tallinn University of Technology (TalTech).

## Curation

Selection is deterministic and balances coverage across dates, time bands,
deployments, and image-derived lighting/contrast/texture/color strata. Split
assignment groups frames from the same source and 10-minute period.

## Known limitations

- Only fish receive object-level bounding boxes.
- `no_fish` means reviewed as containing no fish; it is not a semantic debris
  class and may mix debris, bubbles, sediment, lighting effects, or empty water.
- Date/time metadata are parsed from source paths and filenames and can be
  missing when the naming convention does not encode a valid timestamp.
- Visual-condition bands are coarse image statistics, not field measurements.
- Species labels, flow, rainfall, turbidity, and camera calibration are not
  available consistently.
- Closely related scenes may remain within a split even though 10-minute groups
  prevent the most direct temporal leakage across splits.

## Recommended evaluation

Report fish recall, false-positive rate on hard negatives, precision-recall or
average precision, and results separately by date, time band, and visual
condition. Do not tune against the test split.

## Privacy and sensitivity

The selected imagery is underwater ecological monitoring data and is not
expected to contain people or personal data. Users should still report any
unexpected sensitive content to the repository maintainers.

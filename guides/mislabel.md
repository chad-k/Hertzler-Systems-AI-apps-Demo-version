## What Mislabel Detection does

Look for records whose measurements seem inconsistent with their declared part type or product label.

### A simple example

Suppose two parts have different typical dimensions. A record labeled as Part A but shaped statistically like Part B may indicate a label or data-entry mix-up. It may also be a legitimate unusual item, so it needs a review.

### What you can do in this free demo

Keep the built-in sample data. Check the declared-part column and numeric measurement selections, then run the analysis. Review unusual records, suggested alternative types, comparisons, and visualizations. Adjust the available thresholds to see how sensitivity changes.

The data is synthetic and already included. You can explore the existing filters, settings, charts, and downloads without supplying company files. Changes affect your demonstration session, not production equipment or records.

### How to understand the results

The app first looks for unusual measurements within each declared type using Isolation Forest. It compares a flagged record with other types using standardized differences. A proposed type is an investigation lead. The displayed likelihood-style heuristic is not a scientifically calibrated probability of the true label. PCA is a simplified two-dimensional view of several measurements.

### What the results cannot tell you

Overlapping part dimensions, too few examples, changing processes, or incorrect reference labels can produce misleading suggestions. The app cannot verify the physical identity of an item and does not automatically relabel production records. Select numeric measurement columns, not identifiers or timestamps.

### What a version customized for you would need

Trusted examples for each type, the declared label, relevant dimensions or sensor values, and an agreed review workflow. Domain experts should confirm proposed corrections before any production system is changed.

### Next step

Try the demonstration, then use the contact form at the bottom of this page. Explain your process, what you want to improve, and which results would be useful. Your message goes to Chad at Hertzler; customization is discussed separately from this free demo.

# Multiclass LightGBM Model

This is the secondary classification model. If the binary model detects an attack, pass the network flow to this model to determine the exact attack type (0-7).

Use `label_mapping.pkl` to convert the output number back to a string.

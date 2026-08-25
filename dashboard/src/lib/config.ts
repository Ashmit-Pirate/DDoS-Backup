import { ModelMetadata } from "@/types/sage";

// Static Model Metadata (Not runtime state)
export const MODEL_METADATA: ModelMetadata = {
  name: "Balanced Random Forest",
  featureCount: 77,
  trainedClasses: 8,
  supportedClasses: [
    "Benign",
    "LDAP",
    "MSSQL",
    "NetBIOS",
    "Portmap",
    "Syn",
    "UDP",
    "UDPLag"
  ],
  modelArtifactPath: "/models/ddos_multiclass_random_forest.pkl",
  featureSchemaPath: "/models/ddos_feature_columns.pkl",
  metrics: {
    accuracy: 98.55,
    precision: 75.14,
    recall: 78.46,
    f1: 76.59,
  }
};

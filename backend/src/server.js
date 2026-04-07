import cors from "cors";
import express from "express";
import { readFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { spawn } from "node:child_process";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const rootDir = path.resolve(__dirname, "..", "..");
const modelDir = path.join(rootDir, "model");
const artifactsDir = path.join(modelDir, "artifacts");
const pythonPath = "C:\\Users\\Venkyyy\\AppData\\Local\\Programs\\Python\\Python312\\python.exe";

const app = express();
const port = Number(process.env.PORT || 4000);

app.use(cors());
app.use(express.json());

async function readMetrics() {
  const metricsPath = path.join(artifactsDir, "metrics.json");
  const raw = await readFile(metricsPath, "utf-8");
  return JSON.parse(raw);
}

async function readCatalog() {
  const metadataPath = path.join(artifactsDir, "metadata.json");
  const raw = await readFile(metadataPath, "utf-8");
  const metadata = JSON.parse(raw);

  return {
    symptoms: Object.entries(metadata.symptom_display_map).map(([value, label]) => ({
      value,
      label,
    })),
    metrics: metadata.metrics,
  };
}

function runPrediction(symptoms) {
  return new Promise((resolve, reject) => {
    const scriptPath = path.join(modelDir, "predict.py");
    const symptomArg = symptoms.join(",");
    const subprocess = spawn(pythonPath, [scriptPath, "--symptoms", symptomArg, "--limit", "3"], {
      cwd: modelDir,
    });

    let stdout = "";
    let stderr = "";

    subprocess.stdout.on("data", (chunk) => {
      stdout += chunk.toString();
    });

    subprocess.stderr.on("data", (chunk) => {
      stderr += chunk.toString();
    });

    subprocess.on("close", (code) => {
      if (code !== 0) {
        reject(new Error(stderr || stdout || "Prediction process failed."));
        return;
      }

      try {
        resolve(JSON.parse(stdout));
      } catch (error) {
        reject(new Error(`Invalid prediction payload: ${error.message}`));
      }
    });
  });
}

app.get("/health", async (_request, response) => {
  try {
    const metrics = await readMetrics();
    response.json({
      status: "ok",
      service: "LifeLens AI API",
      modelAccuracy: metrics.maskedAccuracy ?? metrics.accuracy,
      top3Accuracy: metrics.maskedTop3Accuracy ?? metrics.top3Accuracy,
    });
  } catch (error) {
    response.status(500).json({ error: error.message });
  }
});

app.get("/symptoms", async (_request, response) => {
  try {
    const catalog = await readCatalog();
    response.json(catalog);
  } catch (error) {
    response.status(500).json({
      error: "Model artifacts are missing. Run the training script first.",
      detail: error.message,
    });
  }
});

app.post("/predict", async (request, response) => {
  const { symptoms } = request.body ?? {};

  if (!Array.isArray(symptoms) || symptoms.length === 0) {
    response.status(400).json({ error: "Provide a non-empty symptoms array." });
    return;
  }

  try {
    const prediction = await runPrediction(symptoms);
    response.json(prediction);
  } catch (error) {
    response.status(500).json({ error: error.message });
  }
});

const server = app.listen(port, () => {
  console.log(`LifeLens AI API listening on http://localhost:${port}`);
});

server.on("error", (error) => {
  if (error.code === "EADDRINUSE") {
    console.error(`Port ${port} is already in use. Stop the existing backend process or start with a different port, for example: $env:PORT=4001; npm.cmd run start`);
    process.exit(1);
  }

  console.error(error);
  process.exit(1);
});

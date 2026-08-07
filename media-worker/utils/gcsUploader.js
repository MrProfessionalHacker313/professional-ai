/**
 * Google Cloud Storage Uploader
 * Uploads generated media files to GCS bucket on the owner's server.
 */

const { Storage } = require("@google-cloud/storage");
const config = require("../config");

let storage = null;

function getStorage() {
  if (!storage) {
    if (!config.GOOGLE_APPLICATION_CREDENTIALS && !process.env.GOOGLE_APPLICATION_CREDENTIALS) {
      throw new Error("GOOGLE_APPLICATION_CREDENTIALS not configured");
    }
    storage = new Storage({
      projectId: config.GOOGLE_CLOUD_PROJECT,
      keyFilename: config.GOOGLE_APPLICATION_CREDENTIALS,
    });
  }
  return storage;
}

async function uploadFile(localPath, destinationPath) {
  if (!config.GOOGLE_CLOUD_STORAGE_BUCKET) {
    return { success: false, error: "GCS bucket not configured", localPath };
  }

  try {
    const bucket = getStorage().bucket(config.GOOGLE_CLOUD_STORAGE_BUCKET);
    const file = bucket.file(destinationPath);
    await bucket.upload(localPath, { destination: destinationPath, resumable: false });

    // Make public for download (or use signed URLs)
    await file.makePublic();
    const publicUrl = `https://storage.googleapis.com/${config.GOOGLE_CLOUD_STORAGE_BUCKET}/${destinationPath}`;

    return { success: true, url: publicUrl, gcsPath: destinationPath, bucket: config.GOOGLE_CLOUD_STORAGE_BUCKET };
  } catch (err) {
    return { success: false, error: `GCS upload failed: ${err.message}`, localPath };
  }
}

async function deleteFile(destinationPath) {
  if (!config.GOOGLE_CLOUD_STORAGE_BUCKET) return false;
  try {
    const bucket = getStorage().bucket(config.GOOGLE_CLOUD_STORAGE_BUCKET);
    await bucket.file(destinationPath).delete();
    return true;
  } catch {
    return false;
  }
}

module.exports = { uploadFile, deleteFile };

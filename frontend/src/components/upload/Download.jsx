import React, { useEffect, useState } from "react";
import axios from "axios";

const Download = () => {
  const [files, setFiles] = useState([]);
// we will pass cors headers in the axios request
  useEffect(() => {
    axios.get("http://localhost:8000/my-files", { withCredentials: true })
      .then(res => setFiles(res.data))
      .catch(err => console.error(err));
  }, []);

  const downloadFile = async (fileHash, fileName) => {
  try {
    const response = await axios.get(`http://localhost:8000/download`, {
      params: { file_hash: fileHash },
      responseType: 'blob', // crucial for binary data
      headers: {
        Authorization: `Bearer ${localStorage.getItem("token")}`,
      },
      withCredentials: true,
    });

    const blob = new Blob([response.data], { type: "application/octet-stream" });
    const downloadUrl = window.URL.createObjectURL(blob);

    const link = document.createElement("a");
    link.href = downloadUrl;
    link.setAttribute("download", fileName);
    document.body.appendChild(link);
    link.click();
    link.remove();

    window.URL.revokeObjectURL(downloadUrl); // cleanup
  } catch (error) {
    console.error("Download failed", error);
    alert("Error downloading the file");
  }


};

const deleteFile = async (fileHash) => {
  if (!window.confirm("Are you sure you want to delete this file?")) return;

  try {
    await axios.delete("http://localhost:8000/delete-file", {
      params: { file_hash: fileHash },
      headers: {
        Authorization: `Bearer ${localStorage.getItem("token")}`,
      },
      withCredentials: true,
    });

    alert("File deleted successfully");
    // Remove deleted file from UI list
    setFiles((prev) => prev.filter((f) => f.file_hash !== fileHash));
  } catch (error) {
    console.error("Delete failed", error);
    alert("Error deleting the file");
  }
};


  return (
    <div className="p-6 max-w-4xl mx-auto bg-white rounded shadow">
      <h2 className="text-2xl font-bold mb-4">My Files</h2>
      {files.length === 0 ? <p>No files uploaded yet.</p> : (
        <table className="w-full">
          <thead>
            <tr>
              <th className="text-left">File Name</th>
              <th className="text-left">Uploaded</th>
              <th></th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200"> 
            {files.map(file => (
              <tr key={file.file_hash}>
                <td>{file.file_name}</td>
                <td>{new Date(file.uploaded_at).toLocaleString()}</td>
                <td>
                <button
                  className="bg-blue-600 text-white px-3 py-1 rounded mr-2"
                  onClick={() => downloadFile(file.file_hash, file.file_name)}
                >
                  Download
                </button>

                <button
                  className="bg-red-600 text-white px-3 py-1 rounded"
                  onClick={() => deleteFile(file.file_hash)}
                >
                  Delete
                </button>
              </td>

              </tr>
            ))}
          </tbody>
      
        </table>
      )}
    </div>
  );
};

export default Download;
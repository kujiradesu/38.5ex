"use client";

import Head from "next/head";
import { useRouter } from "next/navigation";
import React, { useState } from "react";

export default function Home() {
  const router = useRouter();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");

  const handleLogin = async (e) => {
    e.preventDefault();

    try {
      const response = await fetch("http://127.0.0.1:8000/login", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ username, password }),
        mode: "cors", // 追加: CORSモードを指定
      });

      if (response.ok) {
        const data = await response.json();
        const token = data.access_token;

        // JWTトークンをlocalStorageに保存
        localStorage.setItem("token", token);
        
        // ログイン成功時にホームページにリダイレクト
        router.push("/home");  // ホームページのURLに置き換えてください
      } else {
        const errorData = await response.json();
        console.error("Login failed:", errorData);
        alert("ユーザーネームまたはパスワードが正しくありません");
      }
    } catch (error) {
      console.error("Error logging in:", error);
      alert("エラーが発生しました。");
    }
  };

  const handleBack = () => {
    router.push("/"); // ホームページに戻る
  };

  return (
    <div
      className="flex items-center justify-center min-h-screen"
      style={{ backgroundColor: "#00a4ff", flexDirection: "column" }}
    >
      <Head>
        <title>ログイン画面</title>
      </Head>
      <h1 className="text-4xl mb-8 text-white text-center">Links</h1>
      <div className="text-center text-white w-96">
        <div className="bg-transparent text-white p-8 rounded-lg">
          <h2
            className="text-2xl font-bold mb-6"
            style={{ textAlign: "center", width: "100%" }}
          >
            Linksにログインする
          </h2>
          <form onSubmit={handleLogin}>
            <div className="mb-4">
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="w-full px-3 py-2 border border-white rounded-md focus:outline-none focus:ring-2 focus:ring-white bg-transparent text-white placeholder-white"
                placeholder="ユーザーネーム"
              />
            </div>
            <div className="mb-4">
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full px-3 py-2 border border-white rounded-md focus:outline-none focus:ring-2 focus:ring-white bg-transparent text-white placeholder-white"
                placeholder="パスワード"
              />
            </div>
            <button
              type="submit"
              className="w-full bg-white text-blue-500 py-2 rounded-full mb-2 hover:bg-gray-100 transition duration-200"
            >
              ログイン
            </button>
            <button
              type="button"
              onClick={handleBack}
              className="w-full bg-transparent text-white py-2 rounded-full border border-white hover:bg-white hover:text-blue-500 transition duration-200"
            >
              戻る
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}

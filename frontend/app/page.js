"use client"; // クライアントコンポーネントとして指定

import { useState } from "react";
import { useRouter } from "next/navigation";
import styled from "styled-components";

const HomePage = () => {
  const router = useRouter();

  // useState を使用して、入力内容を管理
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  // ログインボタンがクリックされたときに実行される関数
  const handleLoginClick = () => {
    router.push("/login"); // "/login" へのページ遷移を処理
  };

  // 登録ボタンが押されたときに実行される関数
  const handleRegister = async (e) => {
    e.preventDefault();
    // 入力内容を取得し、サーバーに送信する処理
    try {
      const response = await fetch("http://127.0.0.1:8000/users/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          username: username,
          email: email,
          password: password,
        }),
      });

      if (response.ok) {
        const data = await response.json();
        console.log("ユーザー登録に成功しました:", data);
        // 登録成功後の処理（例: メッセージ表示やページ遷移など）を追加
      } else {
        console.error("ユーザー登録に失敗しました");
      }
    } catch (error) {
      console.error("エラーが発生しました:", error);
    }
  };

  return (
    <Container>
      <LeftSection>
        <Title>Links</Title>
        <Subtitle>
          思いをかたちに、
          <br />
          アイデアを現実に。
        </Subtitle>
      </LeftSection>
      <RightSection>
        <Form onSubmit={handleRegister}>
          <FormTitle>アカウントを登録する</FormTitle>
          <Input
            type="text"
            placeholder="ユーザーネーム"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
          />
          <Input
            type="email"
            placeholder="メールアドレス"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
          <Input
            type="password"
            placeholder="パスワード"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
          <Button type="submit">登録</Button>
          <LoginLink>アカウントをお持ちの場合</LoginLink>
          {/* ログインボタンを押すとhandleLoginClickが呼ばれる */}
          <LoginButton onClick={handleLoginClick}>ログイン</LoginButton>
        </Form>
      </RightSection>
    </Container>
  );
};

export default HomePage;

const Container = styled.div`
  display: flex;
  justify-content: center; /* 中央に配置 */
  align-items: center; /* 中央に配置 */
  height: 100vh;
  background-color: #00a4ff;
`;

const ContentWrapper = styled.div`
  display: flex;
  max-width: 1200px;
  width: 100%;
  justify-content: space-between;
  align-items: center;
`;

const LeftSection = styled.div`
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  color: white;
  padding: 20px;
`;

const Title = styled.h1`
  font-size: 80px;
  font-weight: bold;
  margin: 0;
`;

const Subtitle = styled.p`
  font-size: 24px;
  margin: 20px 0 0;
  line-height: 1.5;
`;

const RightSection = styled.div`
  flex: 1;
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 20px; /* 余白を追加 */
`;

const Form = styled.form` /* フォームタグに変更 */
  background-color: transparent; /* 背景を透明に */
  text-align: center;
  width: 320px;
`;

const FormTitle = styled.h2`
  font-size: 18px;
  margin-bottom: 24px;
  color: #ffffff; /* 白い文字 */
`;

const Input = styled.input`
  width: 100%;
  padding: 10px;
  margin-bottom: 16px;
  border-radius: 4px;
  border: 1px solid #ffffff; /* 枠の色を白色 */
  font-size: 16px;
  background-color: #00a4ff; /* 入力欄を背景と同じ青色 */
  color: white; /* テキストは白色 */

  /* プレースホルダーの色を白に指定 */
  &::placeholder {
    color: white;
    opacity: 1; /* 透明度を100%に設定 */
  }
`;

const Button = styled.button`
  width: 100%;
  padding: 12px;
  background-color: #ffffff;
  color: #00a4ff;
  border: none;
  border-radius: 20px; /* 角を丸くする */
  font-size: 16px;
  font-weight: bold;
  cursor: pointer;
  margin-bottom: 16px;
`;

const LoginLink = styled.p`
  margin: 0;
  font-size: 14px;
  color: #ffffff;
`;

const LoginButton = styled.button`
  width: 100%;
  padding: 12px;
  background-color: transparent;
  color: #ffffff;
  border: 1px solid #ffffff;
  border-radius: 4px;
  font-size: 16px;
  cursor: pointer;
`;

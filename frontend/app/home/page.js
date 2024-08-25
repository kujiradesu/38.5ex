"use client";

import React, { useState, useEffect } from "react";
import styled from "styled-components";
import { HomeIcon as HeroHomeIcon, BellIcon, PlusCircleIcon, UserCircleIcon, ChartBarIcon as DashboardIcon } from '@heroicons/react/solid';
import axios from 'axios';

const HomePage = () => {
  const [selected, setSelected] = useState("home");
  const [showPopup, setShowPopup] = useState(false);

  const [jobClass, setJobClass] = useState("業務");
  const [status, setStatus] = useState("やってみたい");
  const [comment, setComment] = useState("ゆる共有");
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [token, setToken] = useState(null);
  const [mapData, setMapData] = useState([]);

  // useEffectでウィンドウサイズに合わせてキャンバスサイズを設定
useEffect(() => {
  const resizeCanvas = () => {
    const canvas = document.getElementById("mapCanvas");
    if (canvas) {
      canvas.width = window.innerWidth - 420; // 左側のサイドバーを考慮した幅
      canvas.height = window.innerHeight; // ウィンドウの高さに合わせる
    }
    if (mapData.length > 0) {
      plotMapData(mapData); // キャンバスサイズ変更後に再プロット
    }
  };

  window.addEventListener("resize", resizeCanvas);
  resizeCanvas(); // 初期ロード時にもキャンバスをリサイズ

  return () => {
    window.removeEventListener("resize", resizeCanvas);
  };
}, [mapData]); // mapDataが変更されたときにもリサイズと再プロットを実行


  // トークンを取得
  useEffect(() => {
    const savedToken = localStorage.getItem("token");
    if (savedToken) {
      setToken(savedToken);
      fetchMapData(savedToken);  // トークンを使ってマップデータを取得
    } else {
      alert("認証トークンが存在しません。ログインしてください。");
      window.location.href = "/login"; // トークンがない場合、ログインページにリダイレクト
    }
  }, []);

  const handleIconClick = (icon) => {
    if (selected === icon) {
      setShowPopup(!showPopup);
    } else {
      setSelected(icon);
      setShowPopup(true);
    }
  };

  const fetchMapData = async (token) => {
    try {
      const response = await axios.get("http://localhost:8000/map/", {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      console.log("取得したマップデータ:", response.data);  // デバッグ用に取得したデータを表示
      setMapData(response.data);  // マップデータを保存
      plotMapData(response.data);  // マップにプロット
    } catch (error) {
      console.error("マップデータの取得に失敗しました:", error);
      alert("マップデータの取得に失敗しました。");
    }
  };
  


// ステータスに応じた色を返す関数
const getStatusColor = (status) => {
  switch (status) {
    case "やってた":
      return "#C3C3C3";
    case "検討中":
      return "#FFE03D";
    case "やってみたい":
      return "#FF7527";
    default:
      return "#FFFFFF";
  }
};

const plotMapData = (data) => {
  const canvas = document.getElementById("mapCanvas");
  if (canvas) {
    const ctx = canvas.getContext("2d");

    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // x, y 座標の最小値と最大値を取得
    const xValues = data.map(point => point.x);
    const yValues = data.map(point => point.y);
    const xMin = Math.min(...xValues);
    const xMax = Math.max(...xValues);
    const yMin = Math.min(...yValues);
    const yMax = Math.max(...yValues);

    console.log("プロットするデータ:", data);  // デバッグ用にプロットデータを表示

    data.forEach((point) => {
      // 座標を正規化
      const normalizedX = (point.x - xMin) / (xMax - xMin);
      const normalizedY = (point.y - yMin) / (yMax - yMin);

      ctx.beginPath();
      ctx.rect(normalizedX * canvas.width - 10, normalizedY * canvas.height - 10, 20, 20);  // 四角形を描画
      ctx.fillStyle = getStatusColor(point.status);  // ステータスに応じた色を設定
      ctx.fill();

      ctx.beginPath();
      ctx.arc(normalizedX * canvas.width, normalizedY * canvas.height, 5, 0, 2 * Math.PI);  // 中央の円を描画
      ctx.fillStyle = "#FF5733";
      ctx.fill();
    });
  }
};





  // フォーム送信処理
  const handleSubmit = async () => {
    if (!token) {
      alert("トークンが存在しません。ログインしてください。");
      window.location.href = "/login";
      return;
    }

    const data = {
      activity_type: jobClass,
      status: status,
      comment: comment,
      title: title,
      description: description,
    };

    try {
      const response = await axios.post("http://localhost:8000/posts/", data, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      console.log("投稿成功:", response.data);
      // フォームのリセット
      setJobClass("業務");
      setStatus("やってみたい");
      setComment("ゆる共有");
      setTitle("");
      setDescription("");
      setShowPopup(false);
    } catch (error) {
      if (error.response && error.response.status === 401) {
        alert("セッションの有効期限が切れています。再度ログインしてください。");
        localStorage.removeItem("token");  // トークンを削除
        window.location.href = "/login";  // ログインページにリダイレクト
      } else {
        console.error("投稿失敗:", error);
        alert("投稿に失敗しました。");
      }
    }
  };

  return (
    <Container>
      <Sidebar>
        <NavButton
          onClick={() => handleIconClick("home")}
          selected={selected === "home"}
        >
          <HeroHomeIcon className="h-8 w-8" />
        </NavButton>
        <NavButton
          onClick={() => handleIconClick("notifications")}
          selected={selected === "notifications"}
        >
          <BellIcon className="h-8 w-8" />
        </NavButton>
        <NavButton
          onClick={() => handleIconClick("post")}
          selected={selected === "post"}
        >
          <PlusCircleIcon className="h-8 w-8" />
        </NavButton>
        <NavButton
          onClick={() => handleIconClick("profile")}
          selected={selected === "profile"}
        >
          <UserCircleIcon className="h-8 w-8" />
        </NavButton>
        <Spacer />
        <NavButton
          onClick={() => handleIconClick("dashboard")}
          selected={selected === "dashboard"}
        >
          <DashboardIcon className="h-8 w-8" />
        </NavButton>
      </Sidebar>
      <MainContent>
        {showPopup && selected === "home" && (
          <Popup>
            <SearchFieldWrapper>
              <Section>
                <h2>業務/業務外</h2>
                <Description>業務または業務外を選択してください。</Description>
                <ButtonGroup>
                  <Button
                    selected={jobClass === "業務"}
                    onClick={() => setJobClass("業務")}
                  >
                    業務
                  </Button>
                  <Button
                    selected={jobClass === "業務外"}
                    onClick={() => setJobClass("業務外")}
                  >
                    業務外
                  </Button>
                </ButtonGroup>
              </Section>
              <Section>
                <h2>ステータス</h2>
                <Description>ステータスを選択してください。</Description>
                <ButtonGroup>
                  <Button
                    selected={status === "やってた"}
                    onClick={() => setStatus("やってた")}
                  >
                    やってた
                  </Button>
                  <Button
                    selected={status === "活動中"}
                    onClick={() => setStatus("活動中")}
                  >
                    活動中
                  </Button>
                  <Button
                    selected={status === "やってみたい"}
                    onClick={() => setStatus("やってみたい")}
                  >
                    やってみたい
                  </Button>
                </ButtonGroup>
              </Section>
              <Section>
                <h2>コメント</h2>
                <Description>コメントを選択してください。</Description>
                <ButtonGroup>
                  <Button
                    selected={comment === "ゆる共有"}
                    onClick={() => setComment("ゆる共有")}
                  >
                    ゆる共有
                  </Button>
                  <Button
                    selected={comment === "コメントぜひ！"}
                    onClick={() => setComment("コメントぜひ！")}
                  >
                    コメントぜひ！
                  </Button>
                  <Button
                    selected={comment === "仲間募集中！"}
                    onClick={() => setComment("仲間募集中！")}
                  >
                    仲間募集中！
                  </Button>
                </ButtonGroup>
              </Section>
              <Section>
                <h2>キーワード</h2>
                <Description>検索したいキーワードを入力してください。</Description>
                <KeywordWrapper>
                  <InputForm placeholder="マップを検索する" />
                  <SearchButton>検索</SearchButton>
                </KeywordWrapper>
              </Section>
            </SearchFieldWrapper>
          </Popup>
        )}
        {showPopup && selected === "post" && (
          <Popup>
            <PopupTitle>投稿を作成する</PopupTitle>
            <SearchFieldWrapper>
              <Section>
                <h2>業務/業務外</h2>
                <Description>業務または業務外を選択してください。</Description>
                <ButtonGroup>
                  <Button
                    selected={jobClass === "業務"}
                    onClick={() => setJobClass("業務")}
                  >
                    業務
                  </Button>
                  <Button
                    selected={jobClass === "業務外"}
                    onClick={() => setJobClass("業務外")}
                  >
                    業務外
                  </Button>
                </ButtonGroup>
              </Section>
              <Section>
                <h2>ステータス</h2>
                <Description>ステータスを選択してください。</Description>
                <ButtonGroup>
                  <Button
                    selected={status === "やってた"}
                    onClick={() => setStatus("やってた")}
                  >
                    やってた
                  </Button>
                  <Button
                    selected={status === "活動中"}
                    onClick={() => setStatus("活動中")}
                  >
                    活動中
                  </Button>
                  <Button
                    selected={status === "やってみたい"}
                    onClick={() => setStatus("やってみたい")}
                  >
                    やってみたい
                  </Button>
                </ButtonGroup>
              </Section>
              <Section>
                <h2>コメント</h2>
                <Description>コメントを選択してください。</Description>
                <ButtonGroup>
                  <Button
                    selected={comment === "ゆる共有"}
                    onClick={() => setComment("ゆる共有")}
                  >
                    ゆる共有
                  </Button>
                  <Button
                    selected={comment === "コメントぜひ！"}
                    onClick={() => setComment("コメントぜひ！")}
                  >
                    コメントぜひ！
                  </Button>
                  <Button
                    selected={comment === "仲間募集中！"}
                    onClick={() => setComment("仲間募集中！")}
                  >
                    仲間募集中！
                  </Button>
                </ButtonGroup>
              </Section>
              <Section>
                <Description>タイトル</Description>
                <InputForm
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="タイトルを入力する"
                />
              </Section>
              <Section>
                <Description>詳細説明</Description>
                <TextAreaForm
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="詳細説明を入力する"
                />
              </Section>
              <PostButton onClick={handleSubmit}>投稿</PostButton>
            </SearchFieldWrapper>
          </Popup>
        )}
        <MapArea>
          <MapCanvas id="mapCanvas"></MapCanvas>
        </MapArea>
      </MainContent>
    </Container>
  );
};

export default HomePage;

const Container = styled.div`
  display: flex;
  height: 100vh;
  width: 100vw;
  background-color: #2FA6FF;
`;

const Sidebar = styled.div`
  width: 70px;
  background-color: #FFFFFF;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding-top: 20px;
  position: relative;
`;

const NavButton = styled.button`
  background-color: ${(props) => (props.selected ? "#2FA6FF" : "transparent")};
  border: none;
  border-radius: 10px;
  padding: 10px;
  margin-bottom: 20px;
  cursor: pointer;

  &:focus {
    outline: none;
  }

  & svg {
    color: ${(props) => (props.selected ? "#FFFFFF" : "#6D6D6D")};
  }
`;

const Spacer = styled.div`
  flex-grow: 1;
`;

const MainContent = styled.div`
  flex: 1;
  position: relative;
  overflow: hidden;
`;

const Popup = styled.div`
  position: absolute;
  top: 50%;
  left: 1%;
  transform: translateY(-50%);
  background-color: #FFFFFF;
  padding: 30px;
  box-shadow: 0px 0px 10px rgba(0, 0, 0, 0.1);
  border-radius: 8px;
  width: 400px;
  z-index: 1000;
`;

const PopupTitle = styled.h1`
  font-size: 24px;
  font-weight: bold;
  color: #6D6D6D;
  margin-bottom: 20px;
`;

const SearchFieldWrapper = styled.div`
  display: flex;
  flex-direction: column;
`;

const Section = styled.div`
  margin-bottom: 5px;
`;

const Description = styled.p`
  font-size: 12px;
  color: #6D6D6D;
  margin-bottom: 10px;
`;

const ButtonGroup = styled.div`
  display: flex;
  gap: 10px;
`;

const Button = styled.button`
  border: 1px solid #ABABAB;
  border-radius: 25px;
  padding: 5px 10px;
  font-size: 12px;
  color: ${(props) => (props.selected ? "#FFFFFF" : "#6D6D6D")};
  background-color: ${(props) => (props.selected ? "#2FA6FF" : "transparent")};
  cursor: pointer;

  &:focus {
    outline: none;
  }
`;

const KeywordWrapper = styled.div`
  display: flex;
  align-items: center;
`;

const InputForm = styled.input`
  border: 1px solid #ABABAB;
  border-radius: 5px;
  padding: 10px;
  font-size: 14px;
  color: #6D6D6D;
  width: 100%;
`;

const TextAreaForm = styled.textarea`
  width: 100%;
  height: 150px;
  border: 1px solid #ABABAB;
  border-radius: 5px;
  padding: 10px;
  font-size: 14px;
  color: #6D6D6D;
  resize: none;
`;

const PostButton = styled.button`
  border: none;
  border-radius: 25px;
  padding: 10px 20px;
  font-size: 14px;
  color: #FFFFFF;
  background-color: #2FA6FF;
  cursor: pointer;
  display: block;
  margin: 0 auto;
`;

const MapArea = styled.div`
  position: absolute;
  top: 0;
  left: 420px;
  right: 0;
  bottom: 0;
  background-color: #67D5BA;
  display: flex;
  justify-content: center;
  align-items: center;
`;

const MapCanvas = styled.canvas`
  width: 100%;
  height: 100%;
  background-color: #2FA6FF;
`;

const SearchButton = styled.button`
  border: 1px solid #2FA6FF;
  border-radius: 25px;
  padding: 5px 10px;
  font-size: 12px;
  color: #2FA6FF;
  background-color: transparent;
  cursor: pointer;
  margin-left: 10px;
`;

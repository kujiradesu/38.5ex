"use client";

import React, { useState, useEffect, useRef } from "react";
import styled from "styled-components";
import axios from 'axios';
import { HomeIcon as HeroHomeIcon, BellIcon, PlusCircleIcon, UserCircleIcon, ChartBarIcon, PencilIcon, ArrowLeftIcon as DashboardIcon, UserIcon } from '@heroicons/react/solid';


const HomePage = () => {
  // State Variables
  const [selected, setSelected] = useState("home");
  const [showPopup, setShowPopup] = useState(false);
  const [jobClass, setJobClass] = useState("業務");
  const [status, setStatus] = useState("やってみたい");
  const [comment, setComment] = useState("ゆる共有");
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [token, setToken] = useState(null);
  const [mapData, setMapData] = useState([]);
  const [isDragging, setIsDragging] = useState(false);
  const [startPos, setStartPos] = useState({ x: 0, y: 0 });
  const [canvasOffset, setCanvasOffset] = useState({ x: 0, y: 0 });
  const [viewport, setViewport] = useState({ x: 0, y: 0, width: 3000, height: 3000 });
  const [scale, setScale] = useState(1);
  const canvasRef = useRef(null);
  const [profileData, setProfileData] = useState(null);  // プロフィールデータの状態変数を追加
  const [isEditing, setIsEditing] = useState(false);  // 編集モードの状態
  const [saveMessage, setSaveMessage] = useState('');  // 保存メッセージの状態
  const fileInputRef = useRef(null);
  const [showPlotPopup, setShowPlotPopup] = useState(false); // プロットクリック時のポップアップ
  const [selectedPoint, setSelectedPoint] = useState(null); // クリックされたプロットの情報

  const fetchProfileData = async () => {
    try {
        const response = await axios.get('http://localhost:8000/home', {
            headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
        });
        setProfileData(response.data);
    } catch (error) {
        console.error('プロフィールデータの取得に失敗しました:', error);
        // トークンが無効な場合にログインページにリダイレクトする
        if (error.response && error.response.status === 401) {
            alert("セッションの有効期限が切れています。再度ログインしてください。");
            localStorage.removeItem("token");
            window.location.href = "/login";
        }
    }
  };

  const handleProfileChange = (e) => {
    const { name, value } = e.target;
    setProfileData((prevData) => ({
      ...prevData,
      [name]: value,
    }));
  };
  
   // 画像をタップしたときにファイル選択ダイアログを開く関数
   const handleImageClick = () => {
    fileInputRef.current.click();  // ファイル選択ダイアログを開く
  };

    // 画像ファイルが選択されたときに実行する関数
    const handleFileChange = async (event) => {
      const file = event.target.files[0];
      if (file) {
        const formData = new FormData();
        formData.append("profileImage", file);
  
        try {
          const response = await axios.post("http://localhost:8000/upload", formData, {
            headers: {
              "Content-Type": "multipart/form-data",
              Authorization: `Bearer ${localStorage.getItem('token')}`
            }
          });
          setProfileData((prevData) => ({
            ...prevData,
            profileImage: response.data.profileImageUrl,  // サーバーから返された画像URLを使用
          }));
        } catch (error) {
          console.error("画像アップロードに失敗しました:", error);
        }
      }
    };


    // この部分を修正します（現在のhandleProfileSubmit関数を置き換えます）
    const handleProfileSubmit = async (e) => {
      e.preventDefault();
  
      const updatedProfileData = {
          nickname: profileData.nickname, // 'nickname' カラムに対応
          jobTitle: profileData.jobTitle, // 'job_title' カラムに対応
          jobDescription: profileData.jobDescription, // 'job_description' カラムに対応
          interests: profileData.interests, // 'interests' カラムに対応
          skills: profileData.skills, // 'skills' カラムに対応
          values: profileData.values, // 'values' カラムに対応
          officeFloor: profileData.officeFloor, // 'office_floor' カラムに対応
          profileImage: profileData.profileImage, // 'profile_image' カラムに対応 (適切な形式で送信)
          frequentFloor: profileData.frequentFloor, // 'frequent_floor' カラムに対応
          bio: profileData.bio, // 'bio' カラムに対応
      };
  
      try {
          const response = await axios.put('http://localhost:8000/profile', updatedProfileData, {
              headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
          });
          setSaveMessage('プロフィールが変更されました');
          setIsEditing(false);
      } catch (error) {
          console.error('プロフィールの更新に失敗しました:', error.response.data);
      }
  };
  
  
    


  // Initial setup: Canvas offset and viewport setup
  useEffect(() => {
    const initialX = 10;
    const initialY = -20;
    setCanvasOffset({ 
      x: -initialX * scale + window.innerWidth / 2, 
      y: -initialY * scale + window.innerHeight / 2 
    });
  }, []);
  
  useEffect(() => {
    const canvas = canvasRef.current;
    if (canvas) {
      setViewport({ x: 0, y: 0, width: window.innerWidth, height: window.innerHeight });
      if (mapData.length > 0) {
        plotMapData(mapData);
      }
    }
  }, []);

  // Handle zoom in/out
  const handleWheel = (event) => {
    if (event.metaKey) {
      event.preventDefault();
      const zoomDirection = event.deltaY < 0 ? 1 : -1;
      setScale((prevScale) => Math.min(Math.max(prevScale + zoomDirection * 0.1, 0.5), 5));
    }
  };

  useEffect(() => {
    const canvas = canvasRef.current;
    if (canvas) {
      canvas.addEventListener('wheel', handleWheel, { passive: false });
      return () => canvas.removeEventListener('wheel', handleWheel);
    }
  }, []);

  // Handle drag functionality
  const handleMouseDown = (event) => {
    setIsDragging(true);
    setStartPos({ x: event.clientX, y: event.clientY });
  };

  const handleMouseUp = () => {
    setIsDragging(false);
  };

  const handleMouseMove = (event) => {
    if (!isDragging) return;
  
    const dx = event.clientX - startPos.x;
    const dy = event.clientY - startPos.y;
  
    setCanvasOffset((prevOffset) => ({
      x: prevOffset.x + dx,
      y: prevOffset.y + dy,
    }));
  
    setStartPos({ x: event.clientX, y: event.clientY });
  };

  // Resize canvas based on window size
  useEffect(() => {
    const resizeCanvas = () => {
      const canvas = canvasRef.current;
      if (canvas) {
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
        if (mapData.length > 0) {
          plotMapData(mapData);
        }
      }
    };
    
    window.addEventListener("resize", resizeCanvas);
    resizeCanvas();
    return () => window.removeEventListener("resize", resizeCanvas);
  }, []);

  // Fetch map data
  useEffect(() => {
    const savedToken = localStorage.getItem("token");
    if (savedToken) {
      setToken(savedToken);
      fetchMapData(savedToken);
      fetchProfileData();  // プロフィールデータも一緒に取得

      const resizeCanvas = () => {
        const canvas = canvasRef.current;
        if (canvas) {
          canvas.width = window.innerWidth;
          canvas.height = window.innerHeight;
  
          if (mapData.length > 0) {
            plotMapData(mapData);  // キャンバスを再描画
          }
        }
      };
  
      // リサイズ時のデバウンス処理
      const handleResize = debounce(() => {
        resizeCanvas();  // リサイズ時にキャンバスを再設定
      }, 200);
  
      // イベントリスナーの設定
      window.addEventListener("resize", handleResize);
      resizeCanvas();  // 初期ロード時にキャンバスを設定
  
      // クリーンアップ関数
      return () => {
        window.removeEventListener("resize", handleResize);
      };
    } else {
      alert("認証トークンが存在しません。ログインしてください。");
      window.location.href = "/login";
    }
  }, []);

  const fetchMapData = async (token) => {
    try {
        const response = await axios.get("http://localhost:8000/home/", {
            headers: {
                Authorization: `Bearer ${token}`,
            },
        });
        console.log("Fetched map data:", response.data);
        setMapData(response.data);
        plotMapData(response.data);  // データをプロット
    } catch (error) {
        console.error("マップデータの取得に失敗しました:", error);
        alert("マップデータの取得に失敗しました。");
    }
  };

    // Handle form submission
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
          const response = await axios.post("http://localhost:8000/home/", data, {
              headers: {
                  Authorization: `Bearer ${token}`,
              },
          });
  
          // フォームのリセット
          setJobClass("業務");
          setStatus("やりたいこと");
          setComment("ゆる共有");
          setTitle("");
          setDescription("");
          setShowPopup(false);
  
          // 新しいデータを取得して即時反映
          fetchMapData(token);
      } catch (error) {
          if (error.response && error.response.status === 401) {
              alert("セッションの有効期限が切れています。再度ログインしてください。");
              localStorage.removeItem("token");
              window.location.href = "/login";
          } else {
              console.error("投稿失敗:", error);
              alert("投稿に失敗しました。");
          }
      }
  };
  
  const toggleEditing = () => {
    setIsEditing(!isEditing);
  };

  // Plot map data
  const plotMapData = (data) => {
    const canvas = canvasRef.current;
    const rectSize = 50; // 例えば50ピクセルの正方形サイズ
  
    if (canvas) {
      const ctx = canvas.getContext("2d");
      ctx.clearRect(0, 0, canvas.width, canvas.height);
  
      const xValues = data.map(point => point.x);
      const yValues = data.map(point => point.y);
      const xMin = Math.min(...xValues);
      const xMax = Math.max(...xValues);
      const yMin = Math.min(...yValues);
      const yMax = Math.max(...yValues);
  
      const padding = 50;
      const scaleX = (canvas.width - 2 * padding) / (xMax - xMin);
      const scaleY = (canvas.height - 2 * padding) / (yMax - yMin);
      const scale = Math.min(scaleX, scaleY);
  
      const offsetX = padding - xMin * scale;
      const offsetY = padding - yMin * scale;
  
      // データポイントの描画
      data.forEach((point) => {
        const canvasX = point.x * scale + offsetX;
        const canvasY = point.y * scale + offsetY;
  
        ctx.fillStyle = "#67D4BA";
        ctx.fillRect(canvasX - rectSize / 2, canvasY - rectSize / 2, rectSize, rectSize);

        ctx.beginPath();
        ctx.arc(canvasX, canvasY, 10, 0, 2 * Math.PI);
        ctx.fillStyle = getStatusColor(point.status);
        ctx.fill();
  
        // プロットにクリックイベントを追加
        canvas.addEventListener("click", (event) => {
          const clickX = event.clientX;
          const clickY = event.clientY;
  
          if (Math.abs(clickX - canvasX) < rectSize / 2 && Math.abs(clickY - canvasY) < rectSize / 2) {
            setSelectedPoint(point);  // クリックされたプロットの情報をセット
            setShowPlotPopup(true);  // ポップアップを表示
          }
        });
      });
    }
  };

  
  const getStatusColor = (status) => {
    switch (status) {
      case "やってたこと":
        return "#C3C3C3";
      case "やってること":
        return "#FFE03D";
      case "やりたいこと":
        return "#FF882F";
      default:
        return "#FFFFFF";
    }
  };

  const handleIconClick = (icon) => {
    console.log(`Icon clicked: ${icon}, current selected: ${selected}`);
    if (selected === icon) {
        setShowPopup(!showPopup);
    } else {
        setSelected(icon);
        setShowPopup(true);
    }
    console.log(`Popup state: ${showPopup}, new selected: ${selected}`);
};

const handleImageUpload = (event) => {
  const file = event.target.files[0];
  if (file) {
    const reader = new FileReader();
    reader.onloadend = () => {
      setProfileData((prevData) => ({
        ...prevData,
        profileImage: reader.result.split(",")[1],  // Base64部分のみを保存
      }));
    };
    reader.readAsDataURL(file);
  }
};

const debounce = (func, delay) => {
  let debounceTimer;
  return function(...args) {
      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(() => func.apply(this, args), delay);
  };
};

useEffect(() => {
  const handleResize = debounce(() => {
      // ここでリサイズ時の再描画処理を行う
      resizeCanvas();
  }, 200);

  window.addEventListener("resize", handleResize);
  return () => window.removeEventListener("resize", handleResize);
}, []);


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
          console.log("Displaying Home popup"),
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
                    selected={status === "やってたこと"}
                    onClick={() => setStatus("やってたこと")}
                  >
                    やってたこと
                  </Button>
                  <Button
                    selected={status === "やってること"}
                    onClick={() => setStatus("やってること")}
                  >
                    やってること
                  </Button>
                  <Button
                    selected={status === "やりたいこと"}
                    onClick={() => setStatus("やりたいこと")}
                  >
                    やりたいこと
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
          console.log("Displaying Home popup"),
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
                    selected={status === "やってたこと"}
                    onClick={() => setStatus("やってたこと")}
                  >
                    やってたこと
                  </Button>
                  <Button
                    selected={status === "やってること"}
                    onClick={() => setStatus("やってること")}
                  >
                    やってること
                  </Button>
                  <Button
                    selected={status === "やりたいこと"}
                    onClick={() => setStatus("やりたいこと")}
                  >
                    やりたいこと
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
        {showPopup && selected === "profile" && profileData && (
          console.log("Displaying Home popup"),
          <Popup>
            <ProfileContainer>
            <ProfileImageWrapper>
                {profileData.profileImage ? (
                  <ProfileImage 
                    src={profileData.profileImage} 
                    alt="プロフィール画像" 
                    className="profile-image-large"
                  />
                ) : (
                  <UserIcon className="h-48 w-48 text-gray-500" />
                )}
                {isEditing && (
                  <>
                    <input
                      type="file"
                      ref={fileInputRef}
                      style={{ display: 'none' }}
                      onChange={handleImageUpload}
                    />
                    <UploadButton onClick={() => fileInputRef.current.click()}>
                      画像アップロード
                    </UploadButton>
                  </>
                )}
              </ProfileImageWrapper>
              <ProfileInfo>
                <h2>{profileData.username}</h2>
                <button onClick={toggleEditing}>
                  {/* Heroiconsの鉛筆アイコンに変更 */}
                  <PencilIcon className="h-6 w-6 text-gray-500" alt="編集" />
                </button>

                {!isEditing ? (
                  <>
                    <p><strong>ニックネーム:</strong> {profileData.nickname}</p>
                    <p><strong>職種:</strong> {profileData.jobTitle}</p>
                    <p><strong>仕事内容:</strong> {profileData.jobDescription}</p>
                    <p><strong>興味のある分野:</strong> {profileData.interests}</p>
                    <p><strong>得意なこと:</strong> {profileData.skills}</p>
                    <p><strong>大事にしていること:</strong> {profileData.values}</p>
                    <p><strong>よく行くフロア:</strong> {profileData.officeFloor}</p>
                  </>
                ) : (
                  <form onSubmit={handleProfileSubmit}>
                    <label>
                      ニックネーム: 
                      <InputForm 
                        type="text" 
                        name="nickname" 
                        value={profileData.nickname || ''} 
                        onChange={handleProfileChange} 
                      />
                    </label>
                    <label>
                      職種: 
                      <InputForm 
                        type="text" 
                        name="jobTitle" 
                        value={profileData.jobTitle || ''} 
                        onChange={handleProfileChange} 
                      />
                    </label>
                    <label>
                      仕事内容:
                      <InputForm 
                        type="text" 
                        name="jobDescription" 
                        value={profileData.jobDescription || ''} 
                        onChange={handleProfileChange} 
                      />
                    </label>
                    <label>
                      興味のある分野:
                      <InputForm 
                        type="text" 
                        name="interests" 
                        value={profileData.interests || ''} 
                        onChange={handleProfileChange} 
                      />
                    </label>
                    <label>
                      得意なこと:
                      <InputForm 
                        type="text" 
                        name="skills" 
                        value={profileData.skills || ''} 
                        onChange={handleProfileChange} 
                      />
                    </label>
                    <label>
                      大事にしていること:
                      <InputForm 
                        type="text" 
                        name="values" 
                        value={profileData.values || ''} 
                        onChange={handleProfileChange} 
                      />
                    </label>
                    <label>
                      よく行くフロア:
                      <InputForm 
                        type="text" 
                        name="officeFloor" 
                        value={profileData.officeFloor || ''} 
                        onChange={handleProfileChange} 
                      />
                    </label>
                    <label>
                      プロフィール画像URL:
                      <InputForm 
                        type="text" 
                        name="profileImage" 
                        value={profileData.profileImage || ''} 
                        onChange={handleProfileChange} 
                      />
                    </label>
                    <PostButton type="submit">変更を保存</PostButton>
                  </form>
                )}

                {saveMessage && <p>保存完了です!</p>}
                
              </ProfileInfo>
            </ProfileContainer>
          </Popup>
        )}


        <MapArea>
          <MapCanvas
            ref={canvasRef}
            width={3000}
            height={3000}
            onMouseDown={handleMouseDown}
            onMouseMove={handleMouseMove}
            onMouseUp={handleMouseUp}
            onMouseLeave={handleMouseUp}
            onWheel={handleWheel}
          ></MapCanvas>
        </MapArea>
        {showPlotPopup && selectedPoint && (
          <Popup>
            <h2>{selectedPoint.title}</h2>
            <p>{selectedPoint.description}</p>
            <PostButton onClick={() => setShowPopup(false)}>閉じる</PostButton>
          </Popup>
        )}

        {showPopup && selected === "post" && (
          <Popup>
                <PopupTitle>投稿を作成する</PopupTitle>
                {/* 投稿フォームの内容 */}
                <SearchFieldWrapper>
                    {/* フォームフィールドなど */}
                </SearchFieldWrapper>
            </Popup>
        )}
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
  overflow: hidden;  // スクロールバーが表示されないように
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
  overflow: hidden;  // 必要に応じてオーバーフローを隠す
`;

const Popup = styled.div`
  position: absolute;
  top: 10%; /* ここを変更して画面内に確実に表示されるようにする */
  left: 10%;
  background-color: #FFFFFF;
  padding: 30px;
  box-shadow: 0px 0px 10px rgba(0, 0, 0, 0.1);
  border-radius: 8px;
  width: 400px;
  height: auto;
  max-height: 80vh;
  overflow-y: auto;
  transition: opacity 0.2s ease-in-out;  // 速いアニメーション
  z-index: 1000; /* z-indexを追加して他の要素に隠れないようにする */
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
  position: relative;
  width: 100%;  // ビューポート幅にフィットさせる
  height: 100%;  // ビューポート高さにフィットさせる
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

const ProfileContainer = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
`;

const ProfileImage = styled.img`
  width: 200px;
  height: 200px;
  border-radius: 50%;
  object-fit: cover;
  margin-bottom: 20px;
`;

const ProfileInfo = styled.div`
  width: 100%;
  text-align: center;

  h2 {
    font-size: 24px;
    font-weight: bold;
    margin-bottom: 20px;
  }

  p, label {
    font-size: 16px;
    margin: 10px 0;
    color: #333;
  }
`;

const UploadButton = styled.button`
  margin-top: 10px;
  padding: 8px 16px;
  font-size: 14px;
  color: #ffffff;
  background-color: #2fa6ff;
  border: none;
  border-radius: 4px;
  cursor: pointer;

  &:hover {
    background-color: #1d8fd8;
  }
`;

const ProfileImageWrapper = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center; /* 中央揃え */
  margin-bottom: 20px; /* 下にスペースを追加 */
`;

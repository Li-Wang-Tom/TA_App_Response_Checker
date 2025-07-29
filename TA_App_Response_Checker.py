import tkinter as tk
from tkinter import ttk
import win32gui
import win32con
import win32process
import psutil
import time
import threading

class WindowResponseTester:
    def __init__(self, root):
        self.root = root
        self.root.title("アプリケーション応答確認ツール")
        self.root.geometry("600x450")
        
        self.create_widgets()
    
    def create_widgets(self):
        # メインフレーム
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # プロセス選択
        process_frame = ttk.LabelFrame(main_frame, text="テスト対象プロセス", padding="5")
        process_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(process_frame, text="プロセス名:").grid(row=0, column=0, sticky=tk.W)
        self.process_var = tk.StringVar(value="notepad.exe")
        ttk.Entry(process_frame, textvariable=self.process_var, width=20).grid(row=0, column=1, padx=5)
        
        ttk.Button(process_frame, text="応答テスト実行", command=self.test_response).grid(row=0, column=2, padx=10)
        
        # 結果表示
        result_frame = ttk.LabelFrame(main_frame, text="テスト結果", padding="5")
        result_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # 結果テキスト
        self.result_text = tk.Text(result_frame, height=12, width=70)
        self.result_text.pack(fill=tk.BOTH, expand=True)
        
        # フリーズ体験ボタン
        freeze_frame = ttk.LabelFrame(main_frame, text="フリーズ体験（このアプリ自体）", padding="5")
        freeze_frame.pack(fill=tk.X)
        
        # フリーズ時間設定
        freeze_setting_frame = ttk.Frame(freeze_frame)
        freeze_setting_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(freeze_setting_frame, text="フリーズ時間(秒):").grid(row=0, column=0, sticky=tk.W)
        self.freeze_duration = tk.StringVar(value="5")
        ttk.Entry(freeze_setting_frame, textvariable=self.freeze_duration, width=8).grid(row=0, column=1, padx=5)
        
        ttk.Button(freeze_setting_frame, text="指定時間フリーズ", command=self.freeze_self).grid(row=0, column=2, padx=10)
        ttk.Button(freeze_setting_frame, text="永久フリーズ(自死)", command=self.infinite_loop).grid(row=0, column=3, padx=5)
        
        # 注意書き
        ttk.Label(freeze_frame, text="※別のアプリからこのアプリをテストしてください", foreground="red").pack(pady=5)
        
        # プリセットボタン
        preset_frame = ttk.Frame(freeze_frame)
        preset_frame.pack(fill=tk.X)
        
        ttk.Label(preset_frame, text="プリセット:").grid(row=0, column=0, sticky=tk.W)
        ttk.Button(preset_frame, text="1秒", command=lambda: self.set_freeze_time(1)).grid(row=0, column=1, padx=2)
        ttk.Button(preset_frame, text="3秒", command=lambda: self.set_freeze_time(3)).grid(row=0, column=2, padx=2)
        ttk.Button(preset_frame, text="5秒", command=lambda: self.set_freeze_time(5)).grid(row=0, column=3, padx=2)
        ttk.Button(preset_frame, text="10秒", command=lambda: self.set_freeze_time(10)).grid(row=0, column=4, padx=2)
        ttk.Button(preset_frame, text="30秒", command=lambda: self.set_freeze_time(30)).grid(row=0, column=5, padx=2)
    
    def set_freeze_time(self, seconds):
        """フリーズ時間プリセット設定"""
        self.freeze_duration.set(str(seconds))
        self.log(f"🎯 フリーズ時間設定: {seconds}秒")
    
    def log(self, message):
        """ログ出力"""
        timestamp = time.strftime("%H:%M:%S")
        self.result_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.result_text.see(tk.END)
        self.root.update()
    
    def get_process_windows(self, pid):
        """指定プロセスのウィンドウ一覧取得"""
        windows = []
        
        def enum_callback(hwnd, _):
            if win32gui.IsWindowVisible(hwnd):
                try:
                    _, found_pid = win32process.GetWindowThreadProcessId(hwnd)
                    if found_pid == pid:
                        title = win32gui.GetWindowText(hwnd)
                        windows.append((hwnd, title))
                except:
                    pass
            return True
        
        try:
            win32gui.EnumWindows(enum_callback, None)
        except:
            pass
        
        return windows
    
    def test_window_response(self, hwnd, title, timeout_ms=2000):
        """個別ウィンドウの応答テスト"""
        try:
            start_time = time.time()
            
            # WM_NULLメッセージ送信
            result = win32gui.SendMessageTimeout(
                hwnd,
                win32con.WM_NULL,  # 何もしないメッセージ
                0, 0,
                win32con.SMTO_ABORTIFHUNG,
                timeout_ms
            )
            
            elapsed = (time.time() - start_time) * 1000  # ミリ秒
            
            if result[0] == 0:
                return False, f"タイムアウト ({timeout_ms}ms)"
            else:
                return True, f"応答OK ({elapsed:.1f}ms)"
                
        except Exception as e:
            return False, f"エラー: {e}"
    
    def test_response(self):
        """応答テスト実行"""
        process_name = self.process_var.get().strip()
        
        if not process_name:
            self.log("❌ プロセス名を入力してください")
            return
        
        self.log(f"🔍 プロセス検索: {process_name}")
        
        def test_thread():
            try:
                # プロセス検索
                target_process = None
                for proc in psutil.process_iter(['pid', 'name']):
                    if proc.info['name'].lower() == process_name.lower():
                        target_process = proc
                        break
                
                if not target_process:
                    self.log(f"❌ プロセスが見つかりません: {process_name}")
                    return
                
                self.log(f"✅ プロセス発見: PID {target_process.pid}")
                
                # ウィンドウ検索
                windows = self.get_process_windows(target_process.pid)
                
                if not windows:
                    self.log("❌ 表示可能なウィンドウが見つかりません")
                    return
                
                self.log(f"🪟 ウィンドウ発見: {len(windows)}個")
                
                # 各ウィンドウをテスト
                for i, (hwnd, title) in enumerate(windows):
                    self.log(f"\n--- ウィンドウ {i+1}: '{title}' ---")
                    self.log(f"ハンドル: 0x{hwnd:08X}")
                    
                    # 複数回テスト
                    for test_num in range(3):
                        success, result_msg = self.test_window_response(hwnd, title)
                        
                        if success:
                            self.log(f"✅ テスト{test_num+1}: {result_msg}")
                        else:
                            self.log(f"❌ テスト{test_num+1}: {result_msg}")
                        
                        time.sleep(0.5)
                
                self.log("\n🎯 テスト完了")
                
            except Exception as e:
                self.log(f"❌ テスト実行エラー: {e}")
        
        threading.Thread(target=test_thread, daemon=True).start()
    
    def freeze_self(self):
        """このアプリを指定時間フリーズさせる"""
        try:
            duration = float(self.freeze_duration.get())
            if duration <= 0:
                self.log("❌ フリーズ時間は正の数値で入力してください")
                return
        except ValueError:
            self.log("❌ フリーズ時間は数値で入力してください")
            return
        
        self.log(f"⚠️ {duration}秒間フリーズします...")
        self.root.update()
        
        # UIスレッドでsleepするとフリーズする
        time.sleep(duration)
        self.log(f"✅ フリーズ解除（{duration}秒経過）")
    
    def infinite_loop(self):
        """死活監視用（警告）"""
        import tkinter.messagebox
        
        response = tk.messagebox.askyesno(
            "警告", 
            "永久フリーズします。\n"
            "この後、タスクマネージャーで強制終了が必要になります。\n\n"
            "実行しますか？"
        )
        
        if response:
            self.log("⚠️ 永久フリーズ開始... このアプリは応答停止します")
            self.root.update()
            
            # 無限ループ（強制終了するまで止まらない）
            while True:
                pass

def main():
    import tkinter.messagebox
    
    root = tk.Tk()
    app = WindowResponseTester(root)
    
    # 使用方法説明
    tk.messagebox.showinfo(
        "使用方法",
        "【応答テスト】\n"
        "1. プロセス名を入力（例: notepad.exe）\n"
        "2. '応答テスト実行'ボタンを押す\n\n"
        "【フリーズテスト】\n"
        "1. フリーズ時間を入力（秒）\n"
        "2. '指定時間フリーズ'ボタンを押す\n"
        "3. 別のアプリから監視テストを実行\n\n"
        "プリセットボタンで時間を簡単設定できます"
    )
    
    root.mainloop()

if __name__ == "__main__":
    main()
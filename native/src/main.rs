#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::sync::Mutex;
use tauri::{Emitter, Manager};
use tauri_plugin_shell::ShellExt;

struct BackendProcess(Mutex<Option<tauri_plugin_shell::process::CommandChild>>);

#[tauri::command]
async fn start_backend(
    app: tauri::AppHandle,
    state: tauri::State<'_, BackendProcess>,
) -> Result<String, String> {
    let cmd = app
        .shell()
        .sidecar("speech-mcp-backend")
        .map_err(|e| format!("Sidecar error: {}", e))?
        .args(["--http", "--port", "10909"]);

    let (mut rx, child) = cmd
        .spawn()
        .map_err(|e| format!("Failed to start backend: {}", e))?;
    *state.0.lock().unwrap() = Some(child);

    let app_handle = app.clone();
    tauri::async_runtime::spawn(async move {
        use tauri_plugin_shell::process::CommandEvent;
        while let Some(event) = rx.recv().await {
            match event {
                CommandEvent::Stdout(line) | CommandEvent::Stderr(line) => {
                    let text = String::from_utf8_lossy(&line);
                    if text.contains("Uvicorn running")
                        || text.contains("Application startup complete")
                    {
                        let _ = app_handle.emit("backend-status", "ready");
                        break;
                    }
                }
                _ => {}
            }
        }
    });

    Ok("Backend starting on port 10909".into())
}

fn main() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_fs::init())
        .plugin(tauri_plugin_process::init())
        .manage(BackendProcess(Mutex::new(None)))
        .invoke_handler(tauri::generate_handler![start_backend])
        .setup(|app| {
            let handle = app.handle().clone();
            tauri::async_runtime::spawn(async move {
                if let Err(e) =
                    start_backend(handle.clone(), handle.state::<BackendProcess>()).await
                {
                    eprintln!("Backend error: {}", e);
                    let _ = handle.emit("backend-status", format!("error: {}", e));
                }
            });
            #[cfg(debug_assertions)]
            if let Some(window) = app.get_webview_window("main") {
                window.open_devtools();
            }
            Ok(())
        })
        .build(tauri::generate_context!())
        .expect("error building tauri application")
        .run(|app, event| {
            if let tauri::RunEvent::Exit = event {
                if let Some(child) = app.state::<BackendProcess>().0.lock().unwrap().take() {
                    let _ = child.kill();
                }
            }
        });
}

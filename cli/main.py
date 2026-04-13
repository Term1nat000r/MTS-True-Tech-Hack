import asyncio
from time import time

import httpx


BASE_URL = "http://localhost:8000/"

in_chat = False

def show_main_menu():
    print("  [1] Создать новый чат")
    print("  [2] Выбрать чат")
    print("  [3] Удалить чат")
    print("  [4] Выйти")
    print("──────────────────────────────────────")

def validate_choice(choice: int) -> bool:
    return 1 <= choice <= 4


def get_choice(message: str) -> int:
    while True:
        try:
            choice = int(input(message))
        except:
            print("Пожалуйста, введите число")
            continue
        return choice

def exit_cli():
    print("Выход из Lua Code Generator...")
    exit()

async def process_main_menu_choice(client: httpx.AsyncClient, choice: int):
    if choice == 1:
        await create_chat(client)
    elif choice == 2:
        await choose_chat(client)
    elif choice == 3:
        await delete_chat(client)

    elif choice == 4:
        exit_cli()


async def main():
    print("\n╔══════════════════════════════════════╗")
    print("║         Lua Code Generator           ║")
    print("╚══════════════════════════════════════╝")

    async with httpx.AsyncClient(base_url=BASE_URL, timeout=180.0) as client:
        global in_chat
        while True:
            if not in_chat:
                show_main_menu()
                choice = get_choice("Выберите пункт меню: ")

                while not validate_choice(choice):
                    print("Неправильный ввод, попробуйте ещё раз...")
                    choice = get_choice("Выберите пункт меню: ")

                await process_main_menu_choice(client, choice)

            else:
                user_input = input("Введите запрос (введите \"выйти\" чтобы закрыть чат): ")

                if user_input.lower() == "выйти":
                    in_chat = False
                else:
                    await send_user_input(client, user_input)

async def print_history(client: httpx.AsyncClient):
    response = await client.get("/get_current_session")
    session_id = response.json()["session_id"]

    response = await client.get(f"/get_history/{session_id}")
    history = response.json()["history"]

    for h in history:
        if h["role"] == "user":
            print("Вы:", h["content"])
        elif h["role"] == "assistant":
            print("Модель:", h["content"])

async def get_current_session_id(client: httpx.AsyncClient):
    session_id = await client.get("/get_current_session")
    return session_id.json()["session_id"]

async def send_user_input(client: httpx.AsyncClient, user_input: str):
    session_id = await get_current_session_id(client)
    response = await client.post("/test_generate",
                                 json={
                                     "header": {
                                         "source_agent": "user",
                                         "session_id": session_id or "",
                                         "status": "new"
                                     },
                                     "payload": {
                                         "raw_prompt": user_input,
                                         "settings": {
                                             "target_language": "ru",
                                             "mode": "code_generation",
                                             "stream": False
                                         },
                                         "history": []
                                     },
                                     "metadata": {
                                         "timestamp": int(time())
                                     }
                                 })
    result = response.json()

    if response.status_code == 500:
        print("Ошибка:", result["detail"]["message"])
        return

    if "message" in result:
        # Уточнение — модель задаёт вопрос
        print("Модель:", result["message"])
    elif "code" in result:
        # Готовый код
        print("Модель:", result["code"])

async def create_chat(client: httpx.AsyncClient):
    # Создать новую сессию
    response = await client.post("/create_session")
    result = response.json()
    session_id = result["session_id"]
    chat_name = result["chat_name"]

    # Сразу её выбрать как активную
    await change_chat(client, session_id)
    print(f"Создан новый чат:", chat_name)

async def change_chat(client: httpx.AsyncClient, session_id: str):
    global in_chat

    await client.post(f"/change_session/{session_id}")

    in_chat = True


async def get_chats(client: httpx.AsyncClient):
    chats = await client.get("/get_sessions")
    return chats.json()["sessions"]

def show_chats(chats):
    for (i, chat) in enumerate(chats, start=1):
        print(f"{i}. {chat}")
    print("──────────────────────────────────────")

async def choose_chat(client: httpx.AsyncClient):
    chats = await get_chats(client)
    if len(chats) == 0:
        print("Нет созданных чатов")
        print("──────────────────────────────────────")
    else:
        show_chats(chats)
        choice = get_choice("Выберите номер чата: ")

        while not (1 <= choice <= len(chats)):
            print("Неправильный ввод, попробуйте ещё раз...")
            choice = get_choice("Выберите номер чата: ")

        session_id = chats[choice - 1]

        await change_chat(client, session_id)

        await print_history(client)

async def delete_chat(client: httpx.AsyncClient):
    chats = await get_chats(client)
    if len(chats) == 0:
        print("Нет созданных чатов")
        print("──────────────────────────────────────")
    else:
        show_chats(chats)
        choice = get_choice("Выберите номер чата: ")

        while not (1 <= choice <= len(chats)):
            print("Неправильный ввод, попробуйте ещё раз...")
            choice = get_choice("Выберите номер чата: ")

        session_id = chats[choice - 1]

        await client.delete(f"/delete_session/{session_id}")
        print("Чат успешно удалён")

if __name__ == "__main__":
    asyncio.run(main())
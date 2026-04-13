import asyncio
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
    return choice >= 1 and choice <= 4

def get_choice() -> int:
    while True:
        try:
            choice = int(input("Выберите пункт меню\n"))
        except:
            print("Пожалуйста, введите число")
            continue
        return choice

def exit_cli():
    print("Выход из Lua Code Generator...")
    exit()

async def process_main_menu_choice(choice: int):
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=180.0) as client:
        if(choice == 1):
            await create_chat(client)
        elif(choice == 2):
            pass
        elif(choice == 3):
            pass
        elif(choice == 4):
            exit_cli()

async def main():
    client = httpx.AsyncClient()

    print("\n╔══════════════════════════════════════╗")
    print("║         Lua Code Generator           ║")
    print("╚══════════════════════════════════════╝")

    while True:
        if not in_chat:
            show_main_menu()
            choice = get_choice()

            while not validate_choice(choice):
                print("Неправильный ввод попробуйте еще раз...")
                choice = get_choice()

            await process_main_menu_choice(choice)

        else:
            pass
            # Получить историю переписки и вывести её
            # Запросить ввод у пользователя
            # Вывести ответ от модели
            # Повторять пока пользователь не прекратит диалог

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
asyncio.run(main())
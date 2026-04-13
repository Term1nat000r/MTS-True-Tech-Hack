import asyncio
import httpx


BASE_URL = "http://localhost:8000/"

def show_main_menu():
    print("\n╔══════════════════════════════════════╗")
    print("║         Lua Code Generator           ║")
    print("╚══════════════════════════════════════╝")
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

def process_main_menu_choice(choice: int):
    if(choice == 1):
        pass
    elif(choice == 2):
        pass
    elif(choice == 3):
        pass
    elif(choice == 4):
        exit_cli()



async def main():
    session_id = None
    client = httpx.AsyncClient()

    in_chat = False

    while True:
        if not in_chat:
            show_main_menu()
            choice = get_choice()

            while not validate_choice(choice):
                print("Неправильный ввод попробуйте еще раз...")
                choice = get_choice()

            process_main_menu_choice(choice)

        else:
            pass
            # Получить историю переписки и вывести её
            # Запросить ввод у пользователя
            # Вывести ответ от модели
            # Повторять пока пользователь не прекратит диалог

asyncio.run(main())
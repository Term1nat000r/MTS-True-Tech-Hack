# knowledge.py

"""
База знаний для агентов генерации и валидации Lua-кода.
Оптимизировано под лимит num_ctx=4096.
"""

MTS_LOWCODE_RULES = """
ОБЯЗАТЕЛЬНЫЕ ПРАВИЛА ПЛАТФОРМЫ (КРИТИЧЕСКИ ВАЖНО СОБЛЮДАТЬ):
1. Версия: Используется Lua 5.5.
2. Обертка скрипта: Весь сгенерированный код должен быть обернут строго в формат: jsonString lua{ -- код }lua.
3. Доступ к переменным: ЗАПРЕЩЕНО использовать JsonPath.
   - Используй wf.vars для переменных схемы.
   - Используй wf.initVariables для стартовых переменных.
4. Массивы: 
   - Создание: _utils.array.new()
   - Объявление: _utils.array.markAsArray(arr)
5. Разрешены только: if...then...else, while...do...end, for...do...end, repeat...until.
"""

MTS_LUA_EXAMPLES = """
ЭТАЛОННЫЕ ПРИМЕРЫ (FEW-SHOT):

Пример 1: Доступ к массиву
Запрос: "Из полученного списка email получи последний."
Код:
jsonString lua{
    return wf.vars.emails[#wf.vars.emails]
}lua

Пример 2: Очистка значений в словаре (for, pairs)
Запрос: "Очисти значения переменных ID и ENTITY_ID"
Код:
jsonString lua{
    local result = wf.vars.RESTbody.result
    for _, filteredEntry in pairs(result) do
        for key, value in pairs(filteredEntry) do
            if key == "ID" or key == "ENTITY_ID" then
                filteredEntry[key] = nil
            end
        end
    end
    return result
}lua

Пример 3: Безопасное создание массива (ipairs)
Запрос: "Отфильтруй элементы, оставь только с Discount"
Код:
jsonString lua{
    local result = _utils.array.new()
    local items = wf.vars.parsedCsv
    for _, item in ipairs(items) do
        if item.Discount ~= "" and item.Discount ~= nil then
            table.insert(result, item)
        end
    end
    return result
}lua
"""

def get_generator_system_prompt(base_prompt: str) -> str:
    return f"{base_prompt}\n\n{MTS_LOWCODE_RULES}\n\n{MTS_LUA_EXAMPLES}"

def get_validator_system_prompt(base_prompt: str) -> str:
    return f"{base_prompt}\n\n{MTS_LOWCODE_RULES}"

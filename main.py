# Author Loik Andrey 7034@balancedv.ru
import pandas as pd
import os

FILE_NAME = 'Анализ установленного МО.xlsx'
NEW_FILE_NAME = 'Загрузка МО по подразделению.xlsx'

def Run ():
    df_result = create_df(FILE_NAME) # Загружаем и подготавливаем DataFrame
    df_write_xlsx(df_result) # Записываем в эксель

def create_df (file):
    """
    :param file_list: Загружаем в DataFrame файлы из file_list
    :param add_name: Добавляем add_name в наименование колонок DataFrame
    :return: df_result Дата фрэйм с данными из файлов
    """
    df = read_excel(file)

    # Добавляем строку со значениями "Внешний" и перемещаем её в начало DataFrame
    df_index = df.index.values.tolist()
    df.loc[''] = 'Внешний'
    df = df.reindex([''] + df_index)
    df.set_index(['Код', 'Номенклатура'], inplace=True)

    # Копируем колонки и прописываем в них значение "Внутренний" в первую стоку
    col_name1 = df.columns[0]
    col_name2 = col_name1+' МО'
    df = df.drop([df.columns[0]], axis=1)
    df [col_name1] = df
    df [col_name2] = df [col_name1]
    df = df.drop([df.columns[0]], axis=1)
    df[col_name1].loc[('Внешний', 'Внешний')] = ('Внутренний')

    # Переименовываем название колонок индексов для корректной записи в эксель
    df.index.names = ['Номенклатура', '']

    # Переименовываем колонки (удаляем из наименования складов " МО") для корректной записи в эксель
    df.columns = df.columns.str.replace(' МО', '')
    return df

def read_excel (file_name):
    """
    Пытаемся прочитать файл xlxs, если не получается, то исправляем ошибку и опять читаем файл
    :param file_name: Имя файла для чтения
    :return: DataFrame
    """

    read_df = pd.read_excel(file_name, header=0, usecols='A,B,G,H', engine='openpyxl')

    print ('Попытка загрузки файла:'+file_name)
    try:
        df = read_df
        return (df)
    except KeyError as Error:
        print (Error)
        df = None
        if str(Error) == "\"There is no item named 'xl/sharedStrings.xml' in the archive\"":
            bug_fix (file_name)
            print('Исправлена ошибка: ', Error, f'в файле: \"{file_name}\"\n')
            df = read_df
            return df
        else:
            print('Ошибка: >>' + str(Error) + '<<')

def bug_fix (file_name):
    """
    Переименовываем не корректное имя файла в архиве excel
    :param file_name: Имя excel файла
    """
    import shutil
    from zipfile import ZipFile
    from rarfile import RarFile

    # Создаем временную папку
    tmp_folder = '/temp/'
    os.makedirs(tmp_folder, exist_ok=True)

    # Распаковываем excel как zip в нашу временную папку и удаляем excel
    try:
        with ZipFile(file_name) as excel_container:
            excel_container.extractall(tmp_folder)
    except:
        with RarFile(file_name) as excel_container:
            excel_container.extractall(tmp_folder)
    os.remove(file_name)

    # Переименовываем файл с неверным названием
    wrong_file_path = os.path.join(tmp_folder, 'xl', 'SharedStrings.xml')
    correct_file_path = os.path.join(tmp_folder, 'xl', 'sharedStrings.xml')
    os.rename(wrong_file_path, correct_file_path)

    # Запаковываем excel обратно в zip и переименовываем в исходный файл
    try:
        shutil.make_archive(f'{FOLDER}/correct_file', 'zip', tmp_folder)
    except:
        shutil.make_archive(f'{FOLDER}/correct_file', 'rar', tmp_folder)
    os.rename(f'{FOLDER}/correct_file.zip', file_name)

def df_write_xlsx(df):
    # Сохраняем в переменные значения конечных строк и столбцов
    row_end, col_end = len(df), len(df.columns)
    row_end_str, col_end_str = str(row_end), str(col_end)

    # Сбрасываем встроенный формат заголовков pandas
    pd.io.formats.excel.ExcelFormatter.header_style = None

    # Создаём эксель и сохраняем данные
    name_file = NEW_FILE_NAME
    sheet_name = 'Данные'  # Наименование вкладки для сводной таблицы
    writer = pd.ExcelWriter(name_file, engine='xlsxwriter')
    workbook = writer.book
    df.to_excel(writer, sheet_name=sheet_name)
    wks1 = writer.sheets[sheet_name]  # Сохраняем в переменную вкладку для форматирования

    # Получаем словари форматов для эксель
    header_format, con_format, border_storage_format_left, border_storage_format_right, \
    name_format, MO_format, data_format = format_custom(workbook)

    # Форматируем таблицу
    wks1.set_default_row(12)
    wks1.set_row(0, 40, header_format)
    wks1.set_row(1, 10, header_format)
    wks1.set_column('A:A', 12, name_format)
    wks1.set_column('B:B', 32, name_format)
    wks1.set_column('C:R', 10, data_format)

    # Делаем жирным рамку между складами
    i = 2
    while i < col_end+2:
        wks1.set_column(i, i, None, border_storage_format_left)
        wks1.set_column(i+1, i+1, None, border_storage_format_right)
        i += 2

    # Объединяем ячейки
    wks1.merge_range(0, 0, 1, 1, None, None)

    # Добавляем фильтр в первую колонку
    wks1.autofilter(1, 0, row_end+1, col_end+1)
    writer.save() # Сохраняем файл
    return

def format_custom(workbook):
    header_format = workbook.add_format({
        'font_name': 'Arial',
        'font_size': '7',
        'align': 'center',
        'valign': 'top',
        'text_wrap': True,
        'bold': True,
        'bg_color': '#F4ECC5',
        'border': True,
        'border_color': '#CCC085'
    })

    border_storage_format_left = workbook.add_format({
        'num_format': '# ### ##0.00',
        'font_name': 'Arial',
        'font_size': '8',
        'left': 2,
        'left_color': '#000000',
        'bottom': True,
        'bottom_color': '#CCC085',
        'top': True,
        'top_color': '#CCC085',
        'right': True,
        'right_color': '#CCC085',
    })
    border_storage_format_right = workbook.add_format({
        'num_format': '# ### ##0.00',
        'font_name': 'Arial',
        'font_size': '8',
        'right': 2,
        'right_color': '#000000',
        'bottom': True,
        'bottom_color': '#CCC085',
        'top': True,
        'top_color': '#CCC085',
        'left': True,
        'left_color': '#CCC085',
    })

    name_format = workbook.add_format({
        'font_name': 'Arial',
        'font_size': '8',
        'align': 'left',
        'valign': 'top',
        'text_wrap': True,
        'bold': False,
        'border': True,
        'border_color': '#CCC085'
    })

    MO_format = workbook.add_format({
        'num_format': '# ### ##0.00;;',
        'bold': True,
        'font_name': 'Arial',
        'font_size': '8',
        'font_color': '#FF0000',
        # 'text_wrap': True,
        'border': True,
        'border_color': '#CCC085'
    })
    data_format = workbook.add_format({
        'num_format': '# ### ##0.00',
        'font_name': 'Arial',
        'font_size': '8',
        'text_wrap': True,
        'border': True,
        'border_color': '#CCC085'
    })
    con_format = workbook.add_format({
        'bg_color': '#FED69C',
    })

    return header_format, con_format, border_storage_format_left, border_storage_format_right, \
           name_format, MO_format, data_format


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    Run()

# See PyCharm help at https://www.jetbrains.com/help/pycharm/

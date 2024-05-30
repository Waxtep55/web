from translate import Translator
from essential_generators import DocumentGenerator

class Generate():
    def generate(self, db, Quotes):
        gen = DocumentGenerator()
        translation = Translator(from_lang='en', to_lang='ru')

        authors = {'Хадзимэ Исаяма': {'Атака Титанов': ['Леви Аккерман', 'Эрен Йегер', 'Микаса Аккерман', 'Гриша Йегер']},
                   'Пушкин Александр Сергеевич': {'Евгений Онегин': ['Онегин', 'Татьяна', 'Ольга', 'Ленский'],
                                                  'Сказка о царе Салтане': ['Царь Салтан', 'Царица', 'Князь Гвидон', 'Царевна Лебедь'],
                                                  'Руслан и Людмила': ['Руслан', 'Людмила', 'Черномор', 'Финн']},
                   'Честер Беннингтон': ['Breaking The Habbit', 'Numb', 'In The End', 'Faint', 'From The Inside'],
                   'Аристотель': ['Метафизика', 'Экономика', 'Риторика', 'Механика', 'Большая этика'],
                   'Ханс Кристиан Андерсен': {'Гадкий утенок': ['Гадкий утенок', 'Мать гадкого утенка', 'Старая утка', 'Дикие гуси'],
                                              'Новое платье короля': ['Король', 'Два ткача', 'Старый честный министр', 'Достойный сановник'],
                                              'Дюймовочка': ['Дюймовочка', 'Женщина', 'Жаба', 'Майский жук']}}
        for author in authors:
            if type(authors[author]).__name__ == 'dict':
                for composition in authors[author]:
                    for character in authors[author][composition]:
                        for _ in range(3):
                            offer = translation.translate(gen.sentence() + gen.sentence() + gen.sentence())
                            quote = Quotes(text=offer, author=author, composition=composition, character=character)
                            try:
                                db.session.add(quote)
                                db.session.commit()
                            except:
                                print("ОШИБКА ДОБАВЛЕНИЯ ЦИТАТЫ!")
            else:
                for composition in authors[author]:
                    for _ in range(3):
                        offer = translation.translate(gen.sentence() + gen.sentence() + gen.sentence())
                        quote = Quotes(text=offer, author=author, composition=composition)
                        try:
                            db.session.add(quote)
                            db.session.commit()
                        except:
                            print("ОШИБКА ДОБАВЛЕНИЯ ЦИТАТЫ!")
        return 1
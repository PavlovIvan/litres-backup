# Резервное копирование с litres. 

Я купил 589 книг с litres.ru. Внезапно мне показалось, что неплохо было-бы сделать резервную копию всех моих накоплений. 

Базируется на litres api версии 3.31

## Что надо для работы
- python
- интернет
- pip install tqdm
- pip install rfc6266

## Как пользоваться

``` bash
./litres-backup.py -u kiltum -p пароль -f ios.epub
```
- -u имя пользователя. То, что вы вводите на сайте или в приложении
- -p пароль. Оно же
- -f формат, в котором забирать книги. Список форматов разный, но для моей коллекции работают следующие 


* 'fb2.zip'
* 'html'
* 'html.zip'
* 'txt'
* 'txt.zip'
* 'rtf.zip'
* 'a4.pdf'
* 'a6.pdf'
* 'mobi.prc'
* 'epub'
* 'ios.epub'

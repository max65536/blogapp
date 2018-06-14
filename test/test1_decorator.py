#Higher-order function
def add(x,y,f):
    return f(x)+f(y)

print(add(-2,5,abs))

#decorator
def log(func):
    def wrapper0(*args,**kw):
        print('call %s():'% func.__name__)
        return func(*args,**kw)
    return wrapper0

def log1(func):
    print('call %s():'% func.__name__)
    return func()

def now():
    print('abcde')

log1(now)
'''
def now():
    print('abcde')
log(now)()

equals=

@log
def now():
    print('abcde')
'''
def log2(text):
    def decorator(func):
        print(func)
        def wrapper(*args,**kw):
            print('%s %s():' % (text, func.__name__))
            return func(*args,**kw)
        return wrapper
    return decorator

@log2('Number 2')
def now2():
    print(2018)
now2()

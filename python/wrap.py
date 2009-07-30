
def wrap(wrapper):
    def wrap_this_function(function):
        def wrapped_function(*arguments, **keywords):
            return wrapper(function(*arguments, **keywords))
        return wrapped_function
    return wrap_this_function

if __name__ == '__main__':

    @wrap(list)
    def foo():
        yield "a"
    print foo()


import random, math

def uniform(left, right):
    unif = random.random()
    return left + unif * (right - left)

def exponential(lamb):
    unif = uniform(0, 1)
    return -math.log(unif, math.e)/lamb

def normal(mu, sigma):
    while True:
        exp = exponential(1)
        unif = uniform(0, 1)
        if unif <= math.pow(math.e, -(exp - 1) ** 2 / 2):
            u = uniform(0, 1)
            if u <= .5:
                s = 1
            else:
                s = -1
            return s * exp * math.sqrt(sigma) + mu


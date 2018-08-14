# Import `os` 
import os
# os.path.join()
desiredPath = './30759'

def xmlNamesPaths(desiredPath):
    for root, _, filenames in os.walk(desiredPath):
        for f in filenames:
            if f.endswith('.xml'):
                filepath = os.path.join(root, f)
                yield os.path.splitext(f)[0], filepath


# for name, path in xmlNamesPaths(desiredPath):
#     print(name, path)


def flatten(lst):
	new_lst = []
	flatten_helper(lst, new_lst)
	return new_lst
 
def flatten_helper(lst, new_lst):
	for element in lst:
		if isinstance(element, list):
			flatten_helper(element, new_lst)
		else:
			new_lst.append(element)


typedef void (*fset) (void*, unsigned __int64, double);
typedef double (*fget) ();


extern "C" _declspec(dllexport)
void fill_01(void* handle, fset set, fget get, unsigned __int64 count)
{
	for (unsigned __int64 i = 0; i < count; i++)
	{
		set(handle, i, get());
	}
}

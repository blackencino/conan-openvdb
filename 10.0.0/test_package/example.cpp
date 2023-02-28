#include <openvdb/io/File.h>
#include <openvdb/io/io.h>
#include <openvdb/openvdb.h>

#include <iostream>
#include <string>

int main(int argc, char *argv[]) {
  if (argc != 2) {
    std::cerr << "USAGE: " << argv[0] << " <file.vdb>" << std::endl;
    return 1;
  }

  std::string filename{argv[1]};

  using namespace openvdb;
  using namespace openvdb::io;

  try {

    openvdb::initialize();
    // Create a VDB file object.
    openvdb::io::File file{filename};
    // Open the file.  This reads the file header, but not any grids.
    file.open();
    // Loop over all grids in the file and retrieve a shared pointer
    // to the one named "ls_icosahedron".  (This can also be done
    // more simply by calling file.readGrid("ls_icosahedron").)
    openvdb::GridBase::Ptr base_grid;
    for (auto name_iter = file.beginName(); name_iter != file.endName();
         ++name_iter) {
      // Read in only the grid we are interested in.
      if (name_iter.gridName() == "ls_icosahedron") {
        base_grid = file.readGrid(name_iter.gridName());
        std::cout << "Found grid " << name_iter.gridName() << std::endl;
      } else {
        std::cout << "skipping grid " << name_iter.gridName() << std::endl;
      }
    }
    file.close();

  } catch (std::exception &exc) {
    std::cerr << "EXCEPTION: " << exc.what() << std::endl;
    return -1;
  } catch (...) {
    std::cerr << "UNKNOWN EXCEPTION" << std::endl;
    return -1;
  }

  return 0;
}

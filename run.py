from fedora.fedora import FedoraObject
from argparse import ArgumentParser

if __name__ == "__main__":
    parser = ArgumentParser(description="Add a dataset to Fedora.")
    parser.add_argument(
        "-f",
        "--path_to_files",
        dest="path",
        help="Specify the path to your file",
        required=True,
    )
    parser.add_argument(
        "-p",
        "--pid",
        dest="pid",
        help="Specify your pid.",
        required=True,
    )
    parser.add_argument(
        "-d",
        "--dsid",
        dest="dsid",
        help="Specify your dsid.",
        required=True
    )
    args = parser.parse_args()
    FedoraObject().replace_datastream(pid=args.pid, dsid=args.dsid, new_file=args.path)

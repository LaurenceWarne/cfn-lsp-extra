import pytest

from cfn_lsp_extra.scrape.markdown_textwrapper import MarkdownTextWrapper


def test_property_parse():
    text = """`InstanceType`  <a name="cfn-ec2-instance-instancetype"></a>
The instance type\. For more information, see [Instance types](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/instance-types.html) in the *Amazon EC2 User Guide*\.  
Default: `m1.small`   
*Required*: No  
*Type*: String"""
    wrapper = MarkdownTextWrapper(width=80)
    wrapper.wrap(text)

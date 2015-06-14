# -*- coding: utf-8 -*-
import scrapy

from scrapy.spider import BaseSpider
from scrapy.selector import HtmlXPathSelector
from scrapy.http import Request,FormRequest
from scrapy.conf import settings
from scrapy.selector import Selector
from scrapy import log
from scrapy.shell import inspect_response


import leancloud

from leancloud import Object
from leancloud import LeanCloudError
from leancloud import Query

from datetime import datetime
from zhFollowee import settings

from zhUnFollowMember.items import ZhunfollowmemberItem
import re

import json
import redis

class UnfollowmemberSpider(scrapy.Spider):
    name = "unFollowMember"
    allowed_domains = ["zhihu.com"]
    start_urls = (
        'http://www.zhihu.com/',
    )

    followeeCountList =[967]
    handle_httpstatus_list = [401,429,500]
    reqLimit =20
    userDataId = '7e6bee8b4c8c826d76230cd6c139fa27'
    userLinkId = 'sublate'
    followeeDataIdList=[]

    def __init__(self):
        leancloud.init(settings.APP_ID, master_key=settings.MASTER_KEY)
        QuestionFollowee = Object.extend('Followee' + self.userDataId)
        questionFollowee = QuestionFollowee()  #
        query = Query(QuestionFollowee)

        query.equal_to('followerLinkId',self.userLinkId)
        curTime = datetime.now()
        query.less_than('createdAt', curTime)
        followeeCount = query.count()
        print "followeeNumbers: %s" % str(questionNum)
        queryLimit = 500
        queryTimes = int(followeeCount +queryLimit -1) / queryLimit
        self.urls = []
        for index in range(queryTimes):
            query = Query(QuestionFollowee)
            query.less_than('createdAt', curTime)
            query.equal_to('followerLinkId',self.userLinkId)
            query.descending('createdAt')
            query.limit(queryLimit)
            query.skip(index * queryLimit)
            query.select('followeeDataId')
            quesRet = query.find()
            for ques in quesRet:
                self.followeeDataIdList.extend(ques.get('followeeDataId'))



    def start_requests(self):
        #print "start_requests ing ......"
        return [Request("http://www.zhihu.com",callback = self.post_login)]

    def post_login(self,response):
       # print "post_login ing ......"
        xsrfvalue = response.xpath('/html/body/input[@name= "_xsrf"]/@value').extract()[0]
        return [FormRequest.from_response(response,
                                          #headers = self.headers,
                                          formdata={
                                              '_xsrf':xsrfvalue,
                                              'email':'958790455@qq.com',
                                              'password':'heamon7@()',
                                              'rememberme': 'y'
                                          },
                                          dont_filter = True,
                                          callback = self.after_login
                                        #  dont_filter = True
                                          )]

    def after_login(self,response):
        #print "after_login ing ....."
        self.urls = ['http://www.zhihu.com/node/MemberFollowBaseV2']


        print "after_login ing ....."
        #inspect_response(response,self)
        #inspect_response(response,self)
        #self.urls = ['http://www.zhihu.com/question/28626263','http://www.zhihu.com/question/22921426','http://www.zhihu.com/question/20123112']
        for index0 ,followeeDataId in enumerate(self.followeeDataIdList):
            if followeeDataId:
                # inspect_response(response,self)
                xsrfValue = response.xpath('/html/body/input[@name= "_xsrf"]/@value').extract()[0]

                reqUrl = self.urls[0]

                # reqTimes = (int(followeeCount)+self.reqLimit-1)/self.reqLimit
                # print "reqTimes %s" %str(reqTimes)
                # for index in reversed(range(reqTimes)):
                #     print "request index: %s"  %str(index)
                yield FormRequest(url =reqUrl,
                                          #headers = self.headers,
                                          meta={'hash_id':followeeDataId,'xsrfValue':xsrfValue},
                                          formdata={
                                              'method':'unfollow_member',
                                              'params':'{"hash_id":"'+ followeeDataId+'"}',
                                              '_xsrf':xsrfValue,

                                          },
                                          dont_filter = True,
                                          callback = self.parsePage
                                          )

    def parsePage(self,response):

        if response.status != 200:
            print "ParsePage HTTPStatusCode: %s Retrying !" %str(response.status)
            yield FormRequest(url =response.request.url,
                                              #headers = self.headers,
                                              meta={'hash_id':response.meta['hash_id'],'xsrfValue':response.meta['xsrfValue']},
                                              formdata={
                                                  'method':'next',
                                                  'params':'{"hash_id":"'+ response.meta['hash_id']+'"}',
                                                  '_xsrf':response.meta['xsrfValue'],

                                              },
                                              dont_filter = True,
                                              callback = self.parsePage
                                              )
        else:
            item =  ZhunfollowmemberItem()

            yield item
